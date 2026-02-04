"""
WebSocket 메시지 스키마 고정 테스트
API 계약 검증
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.ws_messages import (
    AnalyzeProgress,
    AnalyzeRequest,
    AnalyzeResult,
    AnalyzeStep,
    CelebMatch,
    ErrorResponse,
    MessageType,
    PingMessage,
    PongMessage,
    QualityFlags,
    parse_client_message,
)


class TestMessageTypes:
    """메시지 타입 테스트"""
    
    def test_all_message_types_defined(self):
        """모든 메시지 타입 정의됨"""
        expected_types = [
            "analyze_request",
            "ping",
            "analyze_progress",
            "analyze_result",
            "error",
            "pong",
        ]
        
        for msg_type in expected_types:
            assert msg_type in [t.value for t in MessageType]


class TestAnalyzeRequest:
    """AnalyzeRequest 스키마 테스트"""
    
    def test_valid_request(self):
        """유효한 요청"""
        request = AnalyzeRequest(
            image_data="data:image/jpeg;base64,abc123"
        )
        
        assert request.type == MessageType.ANALYZE_REQUEST
        assert request.image_data == "data:image/jpeg;base64,abc123"
        assert request.session_id is None
    
    def test_with_session_id(self):
        """세션 ID 포함 요청"""
        request = AnalyzeRequest(
            image_data="data:image/jpeg;base64,abc123",
            session_id="sess_20240115_a1b2c3d4"
        )
        
        assert request.session_id == "sess_20240115_a1b2c3d4"
    
    def test_missing_image_data(self):
        """이미지 데이터 누락"""
        with pytest.raises(ValidationError):
            AnalyzeRequest()
    
    def test_json_serialization(self):
        """JSON 직렬화"""
        request = AnalyzeRequest(image_data="test")
        json_data = request.model_dump()
        
        assert json_data["type"] == "analyze_request"
        assert json_data["image_data"] == "test"


class TestCelebMatch:
    """CelebMatch 스키마 테스트"""
    
    def test_valid_match(self):
        """유효한 매치"""
        match = CelebMatch(
            celeb_id="celeb_001",
            name="아이유",
            similarity_score=87.5,
            rank=1,
            expression="smile"
        )
        
        assert match.celeb_id == "celeb_001"
        assert match.name == "아이유"
        assert match.similarity_score == 87.5
        assert match.rank == 1
    
    def test_score_bounds(self):
        """점수 범위 검증"""
        # 최소값
        match = CelebMatch(
            celeb_id="test",
            name="테스트",
            similarity_score=0,
            rank=1,
            expression="neutral"
        )
        assert match.similarity_score == 0
        
        # 최대값
        match = CelebMatch(
            celeb_id="test",
            name="테스트",
            similarity_score=100,
            rank=1,
            expression="neutral"
        )
        assert match.similarity_score == 100
    
    def test_invalid_score(self):
        """유효하지 않은 점수"""
        with pytest.raises(ValidationError):
            CelebMatch(
                celeb_id="test",
                name="테스트",
                similarity_score=150,  # 100 초과
                rank=1,
                expression="neutral"
            )
    
    def test_rank_bounds(self):
        """순위 범위 검증"""
        # 유효한 순위
        for rank in [1, 2, 3]:
            match = CelebMatch(
                celeb_id="test",
                name="테스트",
                similarity_score=80,
                rank=rank,
                expression="neutral"
            )
            assert match.rank == rank


class TestQualityFlags:
    """QualityFlags 스키마 테스트"""
    
    def test_default_values(self):
        """기본값"""
        flags = QualityFlags()
        
        assert flags.is_blurry is False
        assert flags.is_dark is False
        assert flags.is_bright is False
        assert flags.face_size_ok is True
        assert flags.face_centered is True
    
    def test_custom_values(self):
        """커스텀 값"""
        flags = QualityFlags(
            is_blurry=True,
            is_dark=True
        )
        
        assert flags.is_blurry is True
        assert flags.is_dark is True


class TestAnalyzeProgress:
    """AnalyzeProgress 스키마 테스트"""
    
    def test_valid_progress(self):
        """유효한 진행 상태"""
        progress = AnalyzeProgress(
            session_id="sess_test",
            step=AnalyzeStep.EXPRESSION_ANALYZED,
            progress_percent=50,
            message="표정 분석 중..."
        )
        
        assert progress.type == MessageType.ANALYZE_PROGRESS
        assert progress.step == AnalyzeStep.EXPRESSION_ANALYZED
        assert progress.progress_percent == 50
    
    def test_progress_bounds(self):
        """진행률 범위 검증"""
        # 0%
        progress = AnalyzeProgress(
            session_id="test",
            step=AnalyzeStep.RECEIVED,
            progress_percent=0,
            message="시작"
        )
        assert progress.progress_percent == 0
        
        # 100%
        progress = AnalyzeProgress(
            session_id="test",
            step=AnalyzeStep.COMPLETED,
            progress_percent=100,
            message="완료"
        )
        assert progress.progress_percent == 100
    
    def test_invalid_progress(self):
        """유효하지 않은 진행률"""
        with pytest.raises(ValidationError):
            AnalyzeProgress(
                session_id="test",
                step=AnalyzeStep.MATCHING,
                progress_percent=150,  # 100 초과
                message="오류"
            )


class TestAnalyzeResult:
    """AnalyzeResult 스키마 테스트"""
    
    def test_valid_result(self):
        """유효한 결과"""
        result = AnalyzeResult(
            session_id="sess_test",
            detected_expression="smile",
            expression_confidence=0.92,
            matches=[
                CelebMatch(
                    celeb_id="celeb_001",
                    name="아이유",
                    similarity_score=87.5,
                    rank=1,
                    expression="smile"
                )
            ],
            quality_flags=QualityFlags(),
            analysis_time_ms=1234
        )
        
        assert result.type == MessageType.ANALYZE_RESULT
        assert result.detected_expression == "smile"
        assert len(result.matches) == 1
        assert result.analysis_time_ms == 1234
    
    def test_empty_matches(self):
        """빈 매치 리스트"""
        result = AnalyzeResult(
            session_id="sess_test",
            detected_expression="neutral",
            expression_confidence=0.5,
            matches=[],
            quality_flags=QualityFlags(),
            analysis_time_ms=500
        )
        
        assert len(result.matches) == 0
    
    def test_timestamp_auto_generated(self):
        """타임스탬프 자동 생성"""
        result = AnalyzeResult(
            session_id="sess_test",
            detected_expression="neutral",
            expression_confidence=0.5,
            matches=[],
            quality_flags=QualityFlags(),
            analysis_time_ms=500
        )
        
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)


class TestErrorResponse:
    """ErrorResponse 스키마 테스트"""
    
    def test_valid_error(self):
        """유효한 에러"""
        error = ErrorResponse(
            error_code="E101",
            message="얼굴이 감지되지 않았습니다"
        )
        
        assert error.type == MessageType.ERROR
        assert error.error_code == "E101"
        assert error.message == "얼굴이 감지되지 않았습니다"
    
    def test_with_details(self):
        """상세 정보 포함 에러"""
        error = ErrorResponse(
            session_id="sess_test",
            error_code="E201",
            message="이미지가 흐립니다",
            details={"blur_score": 50}
        )
        
        assert error.details["blur_score"] == 50


class TestPingPong:
    """Ping/Pong 메시지 테스트"""
    
    def test_ping(self):
        """핑 메시지"""
        ping = PingMessage()
        assert ping.type == MessageType.PING
    
    def test_pong(self):
        """퐁 메시지"""
        pong = PongMessage()
        assert pong.type == MessageType.PONG
        assert pong.timestamp is not None


class TestParseClientMessage:
    """클라이언트 메시지 파싱 테스트"""
    
    def test_parse_analyze_request(self):
        """분석 요청 파싱"""
        data = {
            "type": "analyze_request",
            "image_data": "test_data"
        }
        
        message = parse_client_message(data)
        
        assert isinstance(message, AnalyzeRequest)
        assert message.image_data == "test_data"
    
    def test_parse_ping(self):
        """핑 파싱"""
        data = {"type": "ping"}
        
        message = parse_client_message(data)
        
        assert isinstance(message, PingMessage)
    
    def test_unknown_type_error(self):
        """알 수 없는 타입 에러"""
        data = {"type": "unknown"}
        
        with pytest.raises(ValueError) as exc_info:
            parse_client_message(data)
        
        assert "Unknown message type" in str(exc_info.value)


class TestAnalyzeStep:
    """AnalyzeStep enum 테스트"""
    
    def test_all_steps_defined(self):
        """모든 단계 정의됨"""
        expected_steps = [
            "received",
            "face_detected",
            "expression_analyzed",
            "embedding_extracted",
            "matching",
            "completed",
        ]
        
        for step in expected_steps:
            assert step in [s.value for s in AnalyzeStep]
    
    def test_step_order(self):
        """단계 순서"""
        steps = list(AnalyzeStep)
        
        # RECEIVED가 첫 번째
        assert steps[0] == AnalyzeStep.RECEIVED
        # COMPLETED가 마지막
        assert steps[-1] == AnalyzeStep.COMPLETED
