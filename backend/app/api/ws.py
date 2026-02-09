"""
/ws/analyze WebSocket

Contract v1 (Step0 fixed):
- request:  type="analyze"
- response: type="result" | type="error"
- Step0에서는 progress 전송 금지
"""
from app.core.debug_tools import trace, trace_enabled, brief

import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.errors import BeautyInsideError, ErrorCode
from app.core.logger import get_logger
from app.domain.pipeline.analyze_pipeline import run_analysis
from app.domain.ports.result_repository import IResultRepository
from app.infra.repositories.null_repository import NullRepository
from app.schemas.ws_messages import (
    AnalyzeRequest,
    ErrorResponse,
    PongMessage,
    ResultItem,
    ResultMessage,
    parse_client_message,
)
from app.utils.ids import generate_session_id

logger = get_logger(__name__)

if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

router = APIRouter()

# Repository 패턴: 현재는 NullRepository (저장 안 함)
# 나중에 PostgresRepository, FileLogRepository 등으로 교체 가능
result_repo: IResultRepository = NullRepository()


def _guess_session_seq(data: Optional[dict]) -> tuple[str, int]:
    if not isinstance(data, dict):
        return generate_session_id(), 0
    sid = data.get("session_id") or generate_session_id()
    try:
        seq = int(data.get("seq") or 0)
    except Exception:
        seq = 0
    return sid, seq


def _map_error_code_to_front(code: ErrorCode) -> str:
    mapping = {
        ErrorCode.NO_FACE_DETECTED: "FACE_NOT_FOUND",
        ErrorCode.MULTIPLE_FACES_DETECTED: "MULTIPLE_FACES",
        ErrorCode.IMAGE_TOO_DARK: "TOO_DARK",
        ErrorCode.IMAGE_TOO_BLURRY: "TOO_BLURRY",
        ErrorCode.EXPRESSION_NOT_DETECTED: "EXPRESSION_WEAK",
        ErrorCode.EXPRESSION_LOW_CONFIDENCE: "EXPRESSION_WEAK",
        ErrorCode.TIMEOUT_ERROR: "TIMEOUT",
        ErrorCode.IMAGE_INVALID_FORMAT: "DECODE_FAIL",
        ErrorCode.IMAGE_TOO_LARGE: "DECODE_FAIL",
        ErrorCode.WS_MESSAGE_INVALID: "DECODE_FAIL",
        ErrorCode.WS_CONNECTION_ERROR: "TIMEOUT",
        ErrorCode.INTERNAL_ERROR: "DECODE_FAIL",
        ErrorCode.MODEL_LOAD_ERROR: "DECODE_FAIL",
        ErrorCode.DATABASE_ERROR: "DECODE_FAIL",
    }
    return mapping.get(code, "DECODE_FAIL")


@router.websocket("/ws/analyze")
@trace("ws_analyze")
async def websocket_analyze(websocket: WebSocket):
    await websocket.accept()
    try:
        client = getattr(websocket, "client", None)
        logger.info("WS accepted", data={"client": str(client)})
    except Exception:
        pass

    data: Optional[dict] = None
    sid, seq = generate_session_id(), 0
    log = logger.with_session(sid)

    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=settings.ws_timeout_seconds)
        try:
            logger.info("WS received text", data={"chars": len(raw)})
        except Exception:
            pass

        try:
            data = json.loads(raw)
            try:
                logger.info("WS parsed json", data={"keys": list(data.keys()) if isinstance(data, dict) else None})
            except Exception:
                pass
        except json.JSONDecodeError:
            sid, seq = _guess_session_seq(None)
            await websocket.send_json(ErrorResponse(
                session_id=sid, seq=seq, latency_ms=0,
                error_code="DECODE_FAIL", message="invalid json", details=None
            ).model_dump())
            await websocket.close()
            return

        sid, seq = _guess_session_seq(data)
        log = logger.with_session(sid)

        try:
            msg = parse_client_message(data)
            try:
                if isinstance(msg, AnalyzeRequest):
                    logger.info("WS message validated", data={"type": msg.type, "session_id": msg.session_id, "seq": msg.seq, "image_b64_len": len(msg.image_b64)})
                else:
                    logger.info("WS message validated", data={"type": getattr(msg, "type", None)})
            except Exception:
                pass
        except Exception:
            await websocket.send_json(ErrorResponse(
                session_id=sid, seq=seq, latency_ms=0,
                error_code="DECODE_FAIL", message="invalid message schema", details=None
            ).model_dump())
            await websocket.close()
            return

        if getattr(msg, "type", None) == "ping":
            await websocket.send_json(PongMessage().model_dump(mode="json"))
            await websocket.close()
            return

        assert isinstance(msg, AnalyzeRequest)

        # Step0: progress_callback=None (progress 메시지 금지)
        logger.info("WS starting analysis", data={"session_id": msg.session_id, "seq": msg.seq, "image_b64": brief(msg.image_b64)})
        result = await run_analysis(
            image_data=msg.image_b64,
            session_id=msg.session_id,
            progress_callback=None,
        )

        # Repository Pattern: 현재 NullRepository (저장 안 함)
        await result_repo.save(result)

        items = []
        for i, m in enumerate(result.top_matches[:3]):
            score_100 = int(round(float(m.score)))
            score_100 = max(0, min(100, score_100))
            # 연예인 이미지 URL 생성 (완전한 URL: http://localhost:8000/api/celeb-image/...)
            clean_name = m.name.replace("_original", "")
            celeb_image_url = f"{settings.api_base_url}/api/celeb-image/{clean_name}_01.jpg"
            items.append(ResultItem(
                rank=i + 1,
                celeb_id=m.celeb_id,
                celeb_name=m.name,
                similarity=round(score_100 / 100.0, 2),
                similarity_100=score_100,
                celeb_image_url=celeb_image_url,
            ))

        resp = ResultMessage(
            session_id=msg.session_id,
            seq=msg.seq,
            latency_ms=int(result.analysis_time_ms),
            expression_label=result.detected_expression.value,
            similarity_method="cosine",
            quality_flags=list(getattr(result.quality, "issues", []) or []),
            results=items,
        )

        await websocket.send_json(resp.model_dump())
        await websocket.close()
        log.info("WS analyze done", latency_ms=int(result.analysis_time_ms))

    except asyncio.TimeoutError:
        sid, seq = _guess_session_seq(data)
        await websocket.send_json(ErrorResponse(
            session_id=sid, seq=seq, latency_ms=0,
            error_code="TIMEOUT", message="ws timeout", details=None
        ).model_dump())
        await websocket.close()

    except WebSocketDisconnect:
        log.info("Client disconnected")

    except BeautyInsideError as e:
        sid, seq = _guess_session_seq(data)
        await websocket.send_json(ErrorResponse(
            session_id=sid, seq=seq, latency_ms=0,
            error_code=_map_error_code_to_front(e.code),
            message="analysis error",
            details=None
        ).model_dump())
        await websocket.close()
        log.warning(f"Analysis error: {e.code} - {e.message}")

    except Exception as e:
        sid, seq = _guess_session_seq(data)
        try:
            await websocket.send_json(ErrorResponse(
                session_id=sid, seq=seq, latency_ms=0,
                error_code="DECODE_FAIL", message="server error", details=None
            ).model_dump())
            await websocket.close()
        except Exception:
            pass
        log.exception(f"Unhandled WS error: {e}")
