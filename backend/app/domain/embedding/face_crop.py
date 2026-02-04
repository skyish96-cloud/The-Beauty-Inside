"""
얼굴 크롭/정렬 모듈
최소 ROI 추출
"""
from typing import Optional, Tuple

import cv2
import numpy as np

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def crop_face(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    margin: float = 0.3,
    target_size: Optional[Tuple[int, int]] = None
) -> np.ndarray:
    """
    얼굴 영역 크롭
    
    Args:
        image: 입력 이미지
        bbox: (x, y, w, h) 바운딩 박스
        margin: 여백 비율 (0.3 = 30% 추가)
        target_size: 출력 크기 (width, height), None이면 원본 크기
    
    Returns:
        크롭된 얼굴 이미지
    """
    x, y, w, h = bbox
    img_h, img_w = image.shape[:2]
    
    # 여백 추가
    margin_w = int(w * margin)
    margin_h = int(h * margin)
    
    # 확장된 영역 계산 (이미지 경계 체크)
    x1 = max(0, x - margin_w)
    y1 = max(0, y - margin_h)
    x2 = min(img_w, x + w + margin_w)
    y2 = min(img_h, y + h + margin_h)
    
    # 크롭
    cropped = image[y1:y2, x1:x2]
    
    # 크기 조정
    if target_size is not None:
        cropped = cv2.resize(cropped, target_size, interpolation=cv2.INTER_AREA)
    
    return cropped


def align_face(
    image: np.ndarray,
    left_eye: Tuple[float, float],
    right_eye: Tuple[float, float],
    target_size: Tuple[int, int] = (224, 224)
) -> np.ndarray:
    """
    눈 위치 기반 얼굴 정렬
    
    Args:
        image: 입력 이미지
        left_eye: 왼쪽 눈 좌표 (x, y)
        right_eye: 오른쪽 눈 좌표 (x, y)
        target_size: 출력 크기
    
    Returns:
        정렬된 얼굴 이미지
    """
    # 눈 사이 각도 계산
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    angle = np.degrees(np.arctan2(dy, dx))
    
    # 눈 사이 중심점
    eye_center = (
        (left_eye[0] + right_eye[0]) / 2,
        (left_eye[1] + right_eye[1]) / 2
    )
    
    # 회전 행렬 계산
    rotation_matrix = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
    
    # 회전 적용
    aligned = cv2.warpAffine(
        image,
        rotation_matrix,
        (image.shape[1], image.shape[0]),
        flags=cv2.INTER_CUBIC
    )
    
    # 크기 조정
    aligned = cv2.resize(aligned, target_size, interpolation=cv2.INTER_AREA)
    
    return aligned


def extract_face_from_landmarks(
    image: np.ndarray,
    landmarks: list,
    target_size: Tuple[int, int] = (224, 224)
) -> Optional[np.ndarray]:
    """
    랜드마크 기반 얼굴 추출
    
    Args:
        image: 입력 이미지
        landmarks: MediaPipe 랜드마크 리스트
        target_size: 출력 크기
    
    Returns:
        추출된 얼굴 이미지 또는 None
    """
    if not landmarks:
        return None
    
    img_h, img_w = image.shape[:2]
    
    # 랜드마크에서 바운딩 박스 계산
    x_coords = [lm["x"] * img_w for lm in landmarks]
    y_coords = [lm["y"] * img_h for lm in landmarks]
    
    x1 = int(min(x_coords))
    y1 = int(min(y_coords))
    x2 = int(max(x_coords))
    y2 = int(max(y_coords))
    
    bbox = (x1, y1, x2 - x1, y2 - y1)
    
    return crop_face(image, bbox, margin=0.2, target_size=target_size)


def get_eye_landmarks(landmarks: list) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    랜드마크에서 눈 좌표 추출
    
    MediaPipe Face Mesh 인덱스:
    - 왼쪽 눈 중심: 468 (또는 33, 133의 평균)
    - 오른쪽 눈 중심: 473 (또는 362, 263의 평균)
    
    Args:
        landmarks: 랜드마크 리스트
    
    Returns:
        ((left_x, left_y), (right_x, right_y)) 또는 None
    """
    if len(landmarks) < 468:
        return None
    
    # 왼쪽 눈 (인덱스 33, 133의 평균)
    left_eye_indices = [33, 133]
    left_x = sum(landmarks[i]["x"] for i in left_eye_indices) / len(left_eye_indices)
    left_y = sum(landmarks[i]["y"] for i in left_eye_indices) / len(left_eye_indices)
    
    # 오른쪽 눈 (인덱스 362, 263의 평균)
    right_eye_indices = [362, 263]
    right_x = sum(landmarks[i]["x"] for i in right_eye_indices) / len(right_eye_indices)
    right_y = sum(landmarks[i]["y"] for i in right_eye_indices) / len(right_eye_indices)
    
    return ((left_x, left_y), (right_x, right_y))


def normalize_face(
    image: np.ndarray,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
) -> np.ndarray:
    """
    얼굴 이미지 정규화 (딥러닝 모델 입력용)
    
    Args:
        image: 0-255 범위의 이미지
        mean: 채널별 평균
        std: 채널별 표준편차
    
    Returns:
        정규화된 이미지
    """
    # 0-1 범위로 변환
    normalized = image.astype(np.float32) / 255.0
    
    # 채널별 정규화
    for i in range(3):
        normalized[:, :, i] = (normalized[:, :, i] - mean[i]) / std[i]
    
    return normalized


class FaceCropper:
    """얼굴 크롭 클래스"""
    
    def __init__(
        self,
        margin: float = 0.3,
        target_size: Tuple[int, int] = (224, 224),
        align: bool = True
    ):
        self.margin = margin
        self.target_size = target_size
        self.align = align
    
    def crop(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        landmarks: Optional[list] = None
    ) -> np.ndarray:
        """
        얼굴 크롭 및 정렬
        
        Args:
            image: 입력 이미지
            bbox: 바운딩 박스
            landmarks: 랜드마크 (정렬에 사용)
        
        Returns:
            처리된 얼굴 이미지
        """
        # 정렬 시도
        if self.align and landmarks:
            eyes = get_eye_landmarks(landmarks)
            if eyes:
                left_eye, right_eye = eyes
                img_h, img_w = image.shape[:2]
                left_eye_px = (left_eye[0] * img_w, left_eye[1] * img_h)
                right_eye_px = (right_eye[0] * img_w, right_eye[1] * img_h)
                return align_face(image, left_eye_px, right_eye_px, self.target_size)
        
        # 일반 크롭
        return crop_face(image, bbox, self.margin, self.target_size)
