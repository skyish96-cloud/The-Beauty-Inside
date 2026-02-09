"""
WebSocket 요청/응답 Pydantic 모델
Contract v1 (Step0 fixed) — 프론트 규격을 그대로 수용
"""
from __future__ import annotations

from app.core.debug_tools import trace, trace_enabled, brief

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union, Literal

from pydantic import BaseModel, Field, ConfigDict


class MessageType(str, Enum):
    # client -> server
    ANALYZE = "analyze"
    PING = "ping"

    # server -> client
    RESULT = "result"
    ERROR = "error"
    PONG = "pong"


class AnalyzeStep(str, Enum):
    """
    (내부용) analyze_pipeline에서만 사용
    Step0에서는 progress 전송 금지라서 프론트로는 안 보냄
    """
    RECEIVED = "received"
    FACE_DETECTED = "face_detected"
    EXPRESSION_ANALYZED = "expression_analyzed"
    EMBEDDING_EXTRACTED = "embedding_extracted"
    MATCHING = "matching"
    COMPLETED = "completed"


# ================== Request (client -> server) ==================

class AnalyzeRequest(BaseModel):
    type: Literal["analyze"] = "analyze"
    session_id: str
    seq: int = Field(..., ge=0)
    ts_ms: int = Field(..., ge=0)
    image_format: Literal["jpeg"] = "jpeg"
    image_b64: str = Field(..., description='NO "data:image/jpeg;base64," prefix')

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "analyze",
                "session_id": "s_9f12ab",
                "seq": 1,
                "ts_ms": 1730000000000,
                "image_format": "jpeg",
                "image_b64": "...."
            }
        }
    )


class PingMessage(BaseModel):
    type: Literal["ping"] = "ping"


# ================== Response (server -> client) ==================

class ResultItem(BaseModel):
    rank: int = Field(..., ge=1, le=3)
    celeb_id: str
    celeb_name: str
    similarity: float = Field(..., ge=0.0, le=1.0)
    similarity_100: int = Field(..., ge=0, le=100)
    celeb_image_url: Optional[str] = None


class ResultMessage(BaseModel):
    type: Literal["result"] = "result"
    session_id: str
    seq: int
    latency_ms: int = Field(..., ge=0)

    expression_label: str
    similarity_method: str = "cosine"
    quality_flags: List[str] = Field(default_factory=list)

    results: List[ResultItem]


class ErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    session_id: str
    seq: int
    latency_ms: int = Field(..., ge=0)

    error_code: str
    message: str
    details: Optional[dict] = None


class PongMessage(BaseModel):
    type: Literal["pong"] = "pong"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@trace("parse_client_message")
def parse_client_message(data: dict) -> Union[AnalyzeRequest, PingMessage]:
    msg_type = data.get("type")
    if msg_type == "analyze":
        return AnalyzeRequest(**data)
    if msg_type == "ping":
        return PingMessage(**data)
    raise ValueError(f"Unknown message type: {msg_type}")
