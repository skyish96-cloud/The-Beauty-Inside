"""
이미지 디코딩 모듈
blob→이미지 디코딩 (형식/크기 제한)
"""
from app.core.debug_tools import trace, trace_enabled, brief

import base64
import io
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.errors import ErrorCode, ImageQualityError
from app.core.logger import get_logger

logger = get_logger(__name__)


if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

# 지원 이미지 형식
SUPPORTED_FORMATS = {"jpeg", "jpg", "png", "webp"}

# 크기 제한
MAX_IMAGE_SIZE = settings.ws_max_message_size  # 10MB
MAX_DIMENSION = 4096  # 최대 해상도
MIN_DIMENSION = 100   # 최소 해상도


@trace("decode_base64_image")
def decode_base64_image(data: str) -> np.ndarray:
    """
    Base64 인코딩된 이미지를 NumPy 배열로 디코딩
    
    Args:
        data: Base64 문자열 (data:image/jpeg;base64,... 형식 지원)
    
    Returns:
        BGR 형식의 NumPy 배열 (OpenCV 호환)
    
    Raises:
        ImageQualityError: 디코딩 실패 또는 형식 오류
    """
    try:
        logger.info("Decode input summary", data={"data": brief(data)})
        # Data URL 형식 처리
        if data.startswith("data:"):
            # data:image/jpeg;base64,/9j/4AAQ... 형식
            header, encoded = data.split(",", 1)
            
            # 형식 검사
            if "image/" in header:
                format_part = header.split("image/")[1].split(";")[0].lower()
                if format_part not in SUPPORTED_FORMATS:
                    raise ImageQualityError(
                        ErrorCode.IMAGE_INVALID_FORMAT,
                        f"지원하지 않는 이미지 형식: {format_part}"
                    )
        else:
            encoded = data
        
        # Base64 디코딩
        image_bytes = base64.b64decode(encoded)
        logger.info("Decoded bytes", data={"bytes_len": len(image_bytes)})

        # 크기 검사
        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise ImageQualityError(
                ErrorCode.IMAGE_TOO_LARGE,
                f"이미지 크기가 너무 큽니다: {len(image_bytes) / 1024 / 1024:.1f}MB"
            )
        
        # NumPy 배열로 변환
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        logger.info("OpenCV imdecode result", data={"is_none": image is None})

        if image is None:
            raise ImageQualityError(
                ErrorCode.IMAGE_INVALID_FORMAT,
                "이미지 디코딩에 실패했습니다"
            )
        
        # 해상도 검사
        height, width = image.shape[:2]
        
        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            raise ImageQualityError(
                ErrorCode.IMAGE_INVALID_FORMAT,
                f"이미지 해상도가 너무 낮습니다: {width}x{height}"
            )
        
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            # 크기 조정
            image = resize_image(image, MAX_DIMENSION)
            logger.debug(f"Image resized from {width}x{height} to {image.shape[1]}x{image.shape[0]}")
        
        return image
        
    except ImageQualityError:
        raise
    except Exception as e:
        logger.error(f"Image decode error: {e}")
        raise ImageQualityError(
            ErrorCode.IMAGE_INVALID_FORMAT,
            f"이미지 처리 중 오류가 발생했습니다: {str(e)}"
        )


@trace("resize_image")
def resize_image(image: np.ndarray, max_dim: int) -> np.ndarray:
    """
    이미지 크기 조정 (비율 유지)
    
    Args:
        image: 입력 이미지
        max_dim: 최대 차원 크기
    
    Returns:
        크기 조정된 이미지
    """
    height, width = image.shape[:2]
    
    if width > height:
        new_width = max_dim
        new_height = int(height * (max_dim / width))
    else:
        new_height = max_dim
        new_width = int(width * (max_dim / height))
    
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    """BGR을 RGB로 변환"""
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
    """RGB를 BGR로 변환"""
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def image_to_base64(image: np.ndarray, format: str = "jpeg", quality: int = 85) -> str:
    """
    NumPy 이미지를 Base64 문자열로 인코딩
    
    Args:
        image: BGR 형식의 이미지
        format: 출력 형식 (jpeg, png)
        quality: JPEG 품질 (1-100)
    
    Returns:
        Base64 인코딩된 문자열
    """
    if format.lower() == "jpeg":
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, quality]
        ext = ".jpg"
    else:
        encode_param = []
        ext = ".png"
    
    _, buffer = cv2.imencode(ext, image, encode_param)
    encoded = base64.b64encode(buffer).decode("utf-8")
    
    return f"data:image/{format};base64,{encoded}"


def get_image_info(image: np.ndarray) -> dict:
    """이미지 정보 반환"""
    height, width = image.shape[:2]
    channels = image.shape[2] if len(image.shape) > 2 else 1
    
    return {
        "width": width,
        "height": height,
        "channels": channels,
        "dtype": str(image.dtype),
        "size_bytes": image.nbytes,
    }
