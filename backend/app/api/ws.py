"""
WebSocket 엔드포인트 모듈
/ws/analyze WebSocket 엔드포인트
"""
import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.errors import BeautyInsideError, ErrorCode, create_error_response
from app.core.logger import get_logger
from app.domain.pipeline.analyze_pipeline import run_analysis
from app.infra.firestore.repo import analysis_repo
from app.schemas.firestore_models import SessionDocument
from app.schemas.ws_messages import (
    AnalyzeProgress,
    AnalyzeResult,
    AnalyzeStep,
    CelebMatch,
    ErrorResponse,
    MessageType,
    PongMessage,
    QualityFlags,
    parse_client_message,
)
from app.utils.ids import generate_session_id

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """연결 수락"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """연결 해제"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_json(self, session_id: str, data: dict):
        """JSON 메시지 전송"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(data)
    
    async def send_progress(
        self,
        session_id: str,
        step: AnalyzeStep,
        percent: int,
        message: str
    ):
        """진행 상태 전송"""
        progress = AnalyzeProgress(
            session_id=session_id,
            step=step,
            progress_percent=percent,
            message=message
        )
        await self.send_json(session_id, progress.model_dump())
    
    async def send_result(self, session_id: str, result: AnalyzeResult):
        """분석 결과 전송"""
        await self.send_json(session_id, result.model_dump(mode="json"))
    
    async def send_error(
        self,
        session_id: str,
        error_code: str,
        message: str,
        details: Optional[dict] = None
    ):
        """에러 전송"""
        error = ErrorResponse(
            session_id=session_id,
            error_code=error_code,
            message=message,
            details=details
        )
        await self.send_json(session_id, error.model_dump())


manager = ConnectionManager()


@router.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """
    얼굴 분석 WebSocket 엔드포인트
    
    클라이언트 → 서버:
    - analyze_request: 이미지 분석 요청
    - ping: 연결 확인
    
    서버 → 클라이언트:
    - analyze_progress: 분석 진행 상태
    - analyze_result: 분석 결과
    - error: 에러
    - pong: 핑 응답
    """
    session_id = generate_session_id()
    log = logger.with_session(session_id)
    
    await manager.connect(websocket, session_id)
    
    # 세션 저장
    await analysis_repo.save_session(SessionDocument(
        session_id=session_id,
        created_at=datetime.utcnow(),
        status="active"
    ))
    
    try:
        while True:
            # 메시지 수신 (타임아웃 적용)
            try:
                raw_data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.ws_timeout_seconds
                )
            except asyncio.TimeoutError:
                log.warning("WebSocket timeout")
                await manager.send_error(
                    session_id,
                    ErrorCode.TIMEOUT_ERROR.value,
                    "연결 시간이 초과되었습니다"
                )
                break
            
            # JSON 파싱
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await manager.send_error(
                    session_id,
                    ErrorCode.WS_MESSAGE_INVALID.value,
                    "잘못된 JSON 형식입니다"
                )
                continue
            
            # 메시지 처리
            msg_type = data.get("type")
            
            if msg_type == MessageType.PING.value:
                # 핑 응답
                pong = PongMessage()
                await manager.send_json(session_id, pong.model_dump(mode="json"))
                
            elif msg_type == MessageType.ANALYZE_REQUEST.value:
                # 분석 요청 처리
                await handle_analyze_request(session_id, data, log)
                
            else:
                await manager.send_error(
                    session_id,
                    ErrorCode.WS_MESSAGE_INVALID.value,
                    f"알 수 없는 메시지 타입: {msg_type}"
                )
    
    except WebSocketDisconnect:
        log.info("Client disconnected")
    except Exception as e:
        log.exception(f"WebSocket error: {e}")
        try:
            await manager.send_error(
                session_id,
                ErrorCode.INTERNAL_ERROR.value,
                "서버 오류가 발생했습니다"
            )
        except:
            pass
    finally:
        manager.disconnect(session_id)


async def handle_analyze_request(session_id: str, data: dict, log):
    """분석 요청 처리"""
    
    image_data = data.get("image_data")
    if not image_data:
        await manager.send_error(
            session_id,
            ErrorCode.WS_MESSAGE_INVALID.value,
            "이미지 데이터가 없습니다"
        )
        return
    
    # 진행 상태 콜백
    async def progress_callback(step: AnalyzeStep, percent: int, message: str):
        await manager.send_progress(session_id, step, percent, message)
    
    # 동기 콜백을 비동기로 래핑
    def sync_progress_callback(step: AnalyzeStep, percent: int, message: str):
        asyncio.create_task(progress_callback(step, percent, message))
    
    try:
        # 분석 실행
        result = await run_analysis(
            image_data=image_data,
            session_id=session_id,
            progress_callback=sync_progress_callback
        )
        
        # 결과 저장
        await analysis_repo.save_full_result(result)
        
        # 결과 전송
        response = AnalyzeResult(
            session_id=session_id,
            detected_expression=result.detected_expression.value,
            expression_confidence=result.expression_confidence,
            matches=[
                CelebMatch(
                    celeb_id=m.celeb_id,
                    name=m.name,
                    similarity_score=m.score,
                    rank=i + 1,
                    expression=m.expression,
                    image_url=m.image_url
                )
                for i, m in enumerate(result.top_matches)
            ],
            quality_flags=QualityFlags(
                is_blurry=result.quality.is_blurry,
                is_dark=result.quality.is_dark,
                is_bright=result.quality.is_bright,
                face_size_ok=result.quality.face_size_ok,
                face_centered=result.quality.face_centered
            ),
            analysis_time_ms=result.analysis_time_ms
        )
        
        await manager.send_result(session_id, response)
        log.info(f"Analysis completed: {len(result.top_matches)} matches")
        
    except BeautyInsideError as e:
        log.warning(f"Analysis error: {e.code} - {e.message}")
        await manager.send_error(
            session_id,
            e.code.value,
            e.message,
            e.details
        )
        
    except Exception as e:
        log.exception(f"Unexpected error: {e}")
        await manager.send_error(
            session_id,
            ErrorCode.INTERNAL_ERROR.value,
            "분석 중 오류가 발생했습니다"
        )
