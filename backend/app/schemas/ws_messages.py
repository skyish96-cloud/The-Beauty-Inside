"""
WebSocket 요청/응답 Pydantic 모델
프론트-백 합의된 API 계약의 소스
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class MessageType(str, Enum):
    """WebSocket 메시지 타입"""
    
    # 클라이언트 → 서버
    ANALYZE_REQUEST = "analyze_request"
    PING = "ping"
    
    # 서버 → 클라이언트
    ANALYZE_PROGRESS = "analyze_progress"
    ANALYZE_RESULT = "analyze_result"
    ERROR = "error"
    PONG = "pong"


class AnalyzeStep(str, Enum):
    """분석 진행 단계"""
    RECEIVED = "received"           # 이미지 수신 완료
    FACE_DETECTED = "face_detected" # 얼굴 감지 완료
    EXPRESSION_ANALYZED = "expression_analyzed"  # 표정 분석 완료
    EMBEDDING_EXTRACTED = "embedding_extracted"  # 임베딩 추출 완료
    MATCHING = "matching"           # 유사 연예인 매칭 중
    COMPLETED = "completed"         # 분석 완료


# ================== 요청 메시지 ==================

class AnalyzeRequest(BaseModel):
    """분석 요청 메시지"""
    type: MessageType = MessageType.ANALYZE_REQUEST
    image_data: str = Field(..., description="Base64 인코딩된 이미지 데이터")
    session_id: Optional[str] = Field(None, description="세션 ID (없으면 서버에서 생성)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "analyze_request",
                "image_data": "data:image/jpeg;base64,/9j/4AAQ...",
                "session_id": "sess_abc123"
            }
        }
    )


class PingMessage(BaseModel):
    """핑 메시지"""
    type: MessageType = MessageType.PING


# ================== 응답 메시지 ==================

class CelebMatch(BaseModel):
    """매칭된 연예인 정보"""
    celeb_id: str = Field(..., description="연예인 고유 ID")
    name: str = Field(..., description="연예인 이름")
    similarity_score: float = Field(..., ge=0, le=100, description="유사도 점수 (0-100)")
    rank: int = Field(..., ge=1, le=3, description="순위 (1=gold, 2=silver, 3=bronze)")
    expression: str = Field(..., description="매칭된 표정")
    image_url: Optional[str] = Field(None, description="연예인 이미지 URL")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "celeb_id": "celeb_001",
                "name": "아이유",
                "similarity_score": 87.5,
                "rank": 1,
                "expression": "smile",
                "image_url": "/celebs/images/smile/celeb_001.jpg"
            }
        }
    )


class QualityFlags(BaseModel):
    """이미지 품질 플래그"""
    is_blurry: bool = False
    is_dark: bool = False
    is_bright: bool = False
    face_size_ok: bool = True
    face_centered: bool = True


class AnalyzeProgress(BaseModel):
    """분석 진행 상태 메시지"""
    type: MessageType = MessageType.ANALYZE_PROGRESS
    session_id: str
    step: AnalyzeStep
    progress_percent: int = Field(..., ge=0, le=100)
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "analyze_progress",
                "session_id": "sess_abc123",
                "step": "expression_analyzed",
                "progress_percent": 50,
                "message": "표정 분석 완료"
            }
        }
    )


class AnalyzeResult(BaseModel):
    """분석 결과 메시지"""
    type: MessageType = MessageType.ANALYZE_RESULT
    session_id: str
    detected_expression: str = Field(..., description="감지된 사용자 표정")
    expression_confidence: float = Field(..., ge=0, le=1, description="표정 감지 신뢰도")
    matches: List[CelebMatch] = Field(..., description="Top 3 매칭 결과")
    quality_flags: QualityFlags
    analysis_time_ms: int = Field(..., description="총 분석 시간 (밀리초)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "analyze_result",
                "session_id": "sess_abc123",
                "detected_expression": "smile",
                "expression_confidence": 0.92,
                "matches": [
                    {"celeb_id": "celeb_001", "name": "아이유", "similarity_score": 87.5, "rank": 1, "expression": "smile"},
                    {"celeb_id": "celeb_002", "name": "수지", "similarity_score": 82.3, "rank": 2, "expression": "smile"},
                    {"celeb_id": "celeb_003", "name": "태연", "similarity_score": 78.1, "rank": 3, "expression": "smile"}
                ],
                "quality_flags": {"is_blurry": False, "is_dark": False, "is_bright": False, "face_size_ok": True, "face_centered": True},
                "analysis_time_ms": 1234,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class ErrorResponse(BaseModel):
    """에러 응답 메시지"""
    type: MessageType = MessageType.ERROR
    session_id: Optional[str] = None
    error_code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="사용자 표시용 에러 메시지")
    details: Optional[dict] = Field(None, description="추가 에러 정보")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "error",
                "session_id": "sess_abc123",
                "error_code": "E101",
                "message": "얼굴이 감지되지 않았습니다.",
                "details": {}
            }
        }
    )


class PongMessage(BaseModel):
    """퐁 메시지"""
    type: MessageType = MessageType.PONG
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ================== 메시지 파싱 ==================

def parse_client_message(data: dict) -> AnalyzeRequest | PingMessage:
    """클라이언트 메시지 파싱"""
    msg_type = data.get("type")
    
    if msg_type == MessageType.ANALYZE_REQUEST.value:
        return AnalyzeRequest(**data)
    elif msg_type == MessageType.PING.value:
        return PingMessage(**data)
    else:
        raise ValueError(f"Unknown message type: {msg_type}")
