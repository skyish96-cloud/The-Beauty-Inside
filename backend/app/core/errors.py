"""
표준 에러/예외 매핑 모듈
에러코드 문서와 1:1 대응
"""
from app.core.debug_tools import trace, trace_enabled, brief

from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """표준 에러 코드 정의"""
    
    # 얼굴 감지 관련 (1xx)
    NO_FACE_DETECTED = "E101"
    MULTIPLE_FACES_DETECTED = "E102"
    FACE_TOO_SMALL = "E103"
    FACE_OUT_OF_FRAME = "E104"
    
    # 이미지 품질 관련 (2xx)
    IMAGE_TOO_BLURRY = "E201"
    IMAGE_TOO_DARK = "E202"
    IMAGE_TOO_BRIGHT = "E203"
    IMAGE_INVALID_FORMAT = "E204"
    IMAGE_TOO_LARGE = "E205"
    
    # 표정 관련 (3xx)
    EXPRESSION_NOT_DETECTED = "E301"
    EXPRESSION_LOW_CONFIDENCE = "E302"
    
    # 시스템 관련 (4xx)
    INTERNAL_ERROR = "E401"
    MODEL_LOAD_ERROR = "E402"
    DATABASE_ERROR = "E403"
    TIMEOUT_ERROR = "E404"
    
    # WebSocket 관련 (5xx)
    WS_CONNECTION_ERROR = "E501"
    WS_MESSAGE_INVALID = "E502"
    WS_SESSION_EXPIRED = "E503"


# 에러 코드별 메시지 매핑
ERROR_MESSAGES = {
    ErrorCode.NO_FACE_DETECTED: "얼굴이 감지되지 않았습니다. 카메라를 정면으로 바라봐 주세요.",
    ErrorCode.MULTIPLE_FACES_DETECTED: "여러 명의 얼굴이 감지되었습니다. 한 명만 촬영해 주세요.",
    ErrorCode.FACE_TOO_SMALL: "얼굴이 너무 작습니다. 카메라에 더 가까이 다가와 주세요.",
    ErrorCode.FACE_OUT_OF_FRAME: "얼굴이 화면 밖에 있습니다. 화면 중앙에 위치해 주세요.",
    
    ErrorCode.IMAGE_TOO_BLURRY: "이미지가 흐립니다. 카메라를 고정하고 다시 촬영해 주세요.",
    ErrorCode.IMAGE_TOO_DARK: "이미지가 너무 어둡습니다. 밝은 곳에서 다시 촬영해 주세요.",
    ErrorCode.IMAGE_TOO_BRIGHT: "이미지가 너무 밝습니다. 조명을 조절해 주세요.",
    ErrorCode.IMAGE_INVALID_FORMAT: "지원하지 않는 이미지 형식입니다.",
    ErrorCode.IMAGE_TOO_LARGE: "이미지 크기가 너무 큽니다.",
    
    ErrorCode.EXPRESSION_NOT_DETECTED: "표정을 인식하지 못했습니다. 다시 시도해 주세요.",
    ErrorCode.EXPRESSION_LOW_CONFIDENCE: "표정 인식 신뢰도가 낮습니다. 표정을 더 뚜렷하게 지어주세요.",
    
    ErrorCode.INTERNAL_ERROR: "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    ErrorCode.MODEL_LOAD_ERROR: "AI 모델 로딩 중 오류가 발생했습니다.",
    ErrorCode.DATABASE_ERROR: "데이터베이스 오류가 발생했습니다.",
    ErrorCode.TIMEOUT_ERROR: "요청 시간이 초과되었습니다.",
    
    ErrorCode.WS_CONNECTION_ERROR: "WebSocket 연결 오류가 발생했습니다.",
    ErrorCode.WS_MESSAGE_INVALID: "잘못된 메시지 형식입니다.",
    ErrorCode.WS_SESSION_EXPIRED: "세션이 만료되었습니다. 다시 연결해 주세요.",
}


class BeautyInsideError(Exception):
    """기본 예외 클래스"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "알 수 없는 오류")
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """에러를 딕셔너리로 변환"""
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details
        }


class FaceDetectionError(BeautyInsideError):
    """얼굴 감지 관련 예외"""
    pass


class ImageQualityError(BeautyInsideError):
    """이미지 품질 관련 예외"""
    pass


class ExpressionError(BeautyInsideError):
    """표정 분석 관련 예외"""
    pass


class SystemError(BeautyInsideError):
    """시스템 관련 예외"""
    pass


class WebSocketError(BeautyInsideError):
    """WebSocket 관련 예외"""
    pass


@trace("create_error_response")
def create_error_response(error: BeautyInsideError) -> dict:
    """에러 응답 생성"""
    return {
        "type": "error",
        "error": error.to_dict()
    }
