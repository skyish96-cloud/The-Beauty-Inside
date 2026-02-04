"""
품질 판단 모듈
"표정 충분?"/흐림/어두움 등 품질 판정
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.core.config import settings
from app.core.errors import ErrorCode, FaceDetectionError, ImageQualityError
from app.core.logger import get_logger
from app.schemas.result_models import QualityResult

logger = get_logger(__name__)


def calculate_blur_score(image: np.ndarray) -> float:
    """
    이미지 흐림 정도 계산 (Laplacian variance)
    
    Args:
        image: BGR 또는 RGB 이미지
    
    Returns:
        흐림 점수 (높을수록 선명)
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    
    return float(variance)


def calculate_brightness(image: np.ndarray) -> float:
    """
    이미지 평균 밝기 계산
    
    Args:
        image: BGR 또는 RGB 이미지
    
    Returns:
        평균 밝기 (0-255)
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    return float(np.mean(gray))


def check_face_size(
    face_bbox: Tuple[int, int, int, int],
    image_shape: Tuple[int, int],
    min_size: int = None
) -> bool:
    """
    얼굴 크기 검사
    
    Args:
        face_bbox: (x, y, w, h) 바운딩 박스
        image_shape: (height, width) 이미지 크기
        min_size: 최소 얼굴 크기 (픽셀)
    
    Returns:
        크기가 충분하면 True
    """
    if min_size is None:
        min_size = settings.min_face_size
    
    _, _, w, h = face_bbox
    return w >= min_size and h >= min_size


def check_face_centered(
    face_bbox: Tuple[int, int, int, int],
    image_shape: Tuple[int, int],
    margin_ratio: float = 0.1
) -> bool:
    """
    얼굴이 화면 중앙에 있는지 검사
    
    Args:
        face_bbox: (x, y, w, h) 바운딩 박스
        image_shape: (height, width) 이미지 크기
        margin_ratio: 허용 여백 비율
    
    Returns:
        중앙에 있으면 True
    """
    x, y, w, h = face_bbox
    img_h, img_w = image_shape
    
    # 얼굴 중심점
    face_cx = x + w / 2
    face_cy = y + h / 2
    
    # 이미지 중심점
    img_cx = img_w / 2
    img_cy = img_h / 2
    
    # 허용 범위
    margin_x = img_w * margin_ratio
    margin_y = img_h * margin_ratio
    
    return (
        abs(face_cx - img_cx) < img_w * 0.3 + margin_x and
        abs(face_cy - img_cy) < img_h * 0.3 + margin_y
    )


def check_image_quality(
    image: np.ndarray,
    face_bbox: Optional[Tuple[int, int, int, int]] = None
) -> QualityResult:
    """
    전체 이미지 품질 검사
    
    Args:
        image: 입력 이미지
        face_bbox: 얼굴 바운딩 박스 (선택)
    
    Returns:
        품질 검사 결과
    """
    result = QualityResult()
    
    # 흐림 검사
    blur_score = calculate_blur_score(image)
    result.blur_score = blur_score
    result.is_blurry = blur_score < settings.blur_threshold
    
    # 밝기 검사
    brightness = calculate_brightness(image)
    result.brightness_score = brightness
    result.is_dark = brightness < settings.brightness_min
    result.is_bright = brightness > settings.brightness_max
    
    # 얼굴 크기/위치 검사
    if face_bbox:
        img_shape = image.shape[:2]
        result.face_size_ok = check_face_size(face_bbox, img_shape)
        result.face_centered = check_face_centered(face_bbox, img_shape)
    
    # 전체 유효성
    result.is_valid = (
        not result.is_blurry and
        not result.is_dark and
        not result.is_bright and
        result.face_size_ok and
        result.face_centered
    )
    
    return result


def validate_face_count(num_faces: int) -> None:
    """
    얼굴 수 검증
    
    Args:
        num_faces: 감지된 얼굴 수
    
    Raises:
        FaceDetectionError: 얼굴이 없거나 여러 명인 경우
    """
    if num_faces == 0:
        raise FaceDetectionError(
            ErrorCode.NO_FACE_DETECTED,
            "얼굴이 감지되지 않았습니다"
        )
    
    if num_faces > settings.max_faces:
        raise FaceDetectionError(
            ErrorCode.MULTIPLE_FACES_DETECTED,
            f"{num_faces}명의 얼굴이 감지되었습니다. 한 명만 촬영해 주세요."
        )


def validate_quality(quality: QualityResult) -> None:
    """
    품질 검증 (에러 발생)
    
    Args:
        quality: 품질 검사 결과
    
    Raises:
        ImageQualityError: 품질 문제 발생 시
    """
    if quality.is_blurry:
        raise ImageQualityError(
            ErrorCode.IMAGE_TOO_BLURRY,
            f"이미지가 흐립니다 (점수: {quality.blur_score:.1f})"
        )
    
    if quality.is_dark:
        raise ImageQualityError(
            ErrorCode.IMAGE_TOO_DARK,
            f"이미지가 너무 어둡습니다 (밝기: {quality.brightness_score:.1f})"
        )
    
    if quality.is_bright:
        raise ImageQualityError(
            ErrorCode.IMAGE_TOO_BRIGHT,
            f"이미지가 너무 밝습니다 (밝기: {quality.brightness_score:.1f})"
        )
    
    if not quality.face_size_ok:
        raise FaceDetectionError(
            ErrorCode.FACE_TOO_SMALL,
            "얼굴이 너무 작습니다"
        )
    
    if not quality.face_centered:
        raise FaceDetectionError(
            ErrorCode.FACE_OUT_OF_FRAME,
            "얼굴이 화면 중앙에 있지 않습니다"
        )


class QualityGate:
    """품질 게이트 클래스"""
    
    def __init__(self, strict: bool = False):
        """
        Args:
            strict: True면 모든 품질 문제에서 에러 발생
        """
        self.strict = strict
    
    def check(
        self,
        image: np.ndarray,
        face_bbox: Optional[Tuple[int, int, int, int]] = None,
        num_faces: int = 1
    ) -> QualityResult:
        """
        품질 검사 수행
        
        Args:
            image: 입력 이미지
            face_bbox: 얼굴 바운딩 박스
            num_faces: 감지된 얼굴 수
        
        Returns:
            품질 검사 결과
        
        Raises:
            FaceDetectionError: 얼굴 관련 문제 (strict 모드)
            ImageQualityError: 이미지 품질 문제 (strict 모드)
        """
        # 얼굴 수 검증
        validate_face_count(num_faces)
        
        # 품질 검사
        quality = check_image_quality(image, face_bbox)
        
        # strict 모드에서는 품질 문제 시 에러 발생
        if self.strict and not quality.is_valid:
            validate_quality(quality)
        
        return quality
