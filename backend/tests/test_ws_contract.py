"""
WebSocket 메시지 스키마 고정 테스트
Contract v1 (Step0 fixed) 검증
"""
from app.core.debug_tools import trace, trace_enabled, brief

import pytest
from pydantic import ValidationError

from app.schemas.ws_messages import (
    AnalyzeRequest,
    ErrorResponse,
    MessageType,
    PingMessage,
    PongMessage,
    ResultItem,
    ResultMessage,
    parse_client_message,
)


class TestMessageTypes:
    def test_all_message_types_defined(self):
        expected = ["analyze", "ping", "result", "error", "pong"]
        for t in expected:
            assert t in [x.value for x in MessageType]


class TestAnalyzeRequest:
    def test_valid_request(self):
        req = AnalyzeRequest(
            session_id="s_test",
            seq=1,
            ts_ms=1730000000000,
            image_format="jpeg",
            image_b64="AAA",
        )
        assert req.type == "analyze"
        assert req.session_id == "s_test"
        assert req.seq == 1

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AnalyzeRequest(session_id="s_test", seq=1, ts_ms=0, image_format="jpeg")  # image_b64 missing

    def test_parse_client_message(self):
        msg = parse_client_message({
            "type": "analyze",
            "session_id": "s_test",
            "seq": 1,
            "ts_ms": 1,
            "image_format": "jpeg",
            "image_b64": "AAA",
        })
        assert isinstance(msg, AnalyzeRequest)

        ping = parse_client_message({"type": "ping"})
        assert isinstance(ping, PingMessage)


class TestResultSchema:
    def test_result_message(self):
        res = ResultMessage(
            session_id="s_test",
            seq=1,
            latency_ms=123,
            expression_label="smile",
            similarity_method="cosine",
            quality_flags=[],
            results=[
                ResultItem(rank=1, celeb_id="c_001", celeb_name="A", similarity=0.82, similarity_100=82),
                ResultItem(rank=2, celeb_id="c_002", celeb_name="B", similarity=0.79, similarity_100=79),
                ResultItem(rank=3, celeb_id="c_003", celeb_name="C", similarity=0.77, similarity_100=77),
            ],
        )
        assert res.type == "result"
        assert len(res.results) == 3


class TestErrorSchema:
    def test_error_message(self):
        err = ErrorResponse(
            session_id="s_test",
            seq=1,
            latency_ms=0,
            error_code="FACE_NOT_FOUND",
            message="x",
            details=None,
        )
        assert err.type == "error"
        assert err.error_code == "FACE_NOT_FOUND"


class TestPongSchema:
    def test_pong(self):
        pong = PongMessage()
        assert pong.type == "pong"
