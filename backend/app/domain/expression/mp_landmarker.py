"""
MediaPipe 초기화/추론 래퍼 모듈
얼굴 랜드마크 및 블렌드쉐이프 추출
"""
from app.core.debug_tools import trace, trace_enabled, brief

from functools import lru_cache
from typing import Optional, List, Dict, Any

import numpy as np

from app.core.config import settings
from app.core.logger import get_logger
from app.core.errors import ErrorCode, FaceDetectionError, ExpressionError
from app.core.model_loader import get_mediapipe_model_path

logger = get_logger(__name__)



if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

# MediaPipe Face Landmarker 지연 로딩
_landmarker = None
_landmarker_initialized = False


@trace("mediapipe._get_landmarker")
def _get_landmarker():
    """MediaPipe FaceLandmarker 인스턴스 반환 (지연 로딩)"""
    global _landmarker, _landmarker_initialized
    
    if _landmarker_initialized:
        return _landmarker
    
    try:
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        # 모델 파일 경로 (자동 다운로드)
        model_path = get_mediapipe_model_path()
        logger.info(f"Loading MediaPipe model from: {model_path}")
        
        base_options = python.BaseOptions(
            model_asset_path=model_path
        )
        
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=settings.max_faces + 1,  # 여러 얼굴 감지용
            min_face_detection_confidence=settings.face_detection_confidence,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        
        _landmarker = vision.FaceLandmarker.create_from_options(options)
        _landmarker_initialized = True
        logger.info("MediaPipe FaceLandmarker initialized")
        
    except Exception as e:
        logger.warning(f"MediaPipe FaceLandmarker initialization failed: {e}")
        _landmarker_initialized = True
        _landmarker = None
    
    return _landmarker


class FaceLandmarkerResult:
    """얼굴 랜드마크 결과"""
    
    def __init__(
        self,
        landmarks: List[Dict[str, float]],
        blendshapes: Dict[str, float],
        face_bbox: tuple,
        confidence: float
    ):
        self.landmarks = landmarks
        self.blendshapes = blendshapes
        self.face_bbox = face_bbox
        self.confidence = confidence


class MediaPipeLandmarker:
    """MediaPipe 얼굴 랜드마크 추출기"""
    
    def __init__(self):
        self._landmarker = None
    
    def _ensure_initialized(self):
        """초기화 확인"""
        if self._landmarker is None:
            self._landmarker = _get_landmarker()
    
    @trace("mediapipe.detect")
    def detect(self, image: np.ndarray) -> List[FaceLandmarkerResult]:
        """
        이미지에서 얼굴 랜드마크 감지
        
        Args:
            image: RGB 형식의 NumPy 배열
        
        Returns:
            감지된 얼굴별 랜드마크 결과 리스트
        
        Raises:
            FaceDetectionError: 얼굴 감지 실패
        """
        self._ensure_initialized()
        try:
            logger.info("MediaPipe detect input", data={"image": brief(image)})
        except Exception:
            pass

        if self._landmarker is None:
            # MediaPipe 사용 불가 시 대체 로직
            return self._detect_fallback(image)
        
        try:
            import mediapipe as mp
            
            # MediaPipe 이미지로 변환
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            
            # 감지 수행
            detection_result = self._landmarker.detect(mp_image)
            try:
                n_faces = len(detection_result.face_landmarks) if detection_result.face_landmarks else 0
                logger.info("MediaPipe raw result", data={"num_faces": n_faces})
            except Exception:
                pass

            if not detection_result.face_landmarks:
                return []
            
            results = []
            for i, face_landmarks in enumerate(detection_result.face_landmarks):
                # 랜드마크 추출
                landmarks = [
                    {"x": lm.x, "y": lm.y, "z": lm.z}
                    for lm in face_landmarks
                ]
                
                # 블렌드쉐이프 추출
                blendshapes = {}
                if detection_result.face_blendshapes and i < len(detection_result.face_blendshapes):
                    for bs in detection_result.face_blendshapes[i]:
                        blendshapes[bs.category_name] = bs.score
                
                # 바운딩 박스 계산
                x_coords = [lm.x for lm in face_landmarks]
                y_coords = [lm.y for lm in face_landmarks]
                h, w = image.shape[:2]
                bbox = (
                    int(min(x_coords) * w),
                    int(min(y_coords) * h),
                    int((max(x_coords) - min(x_coords)) * w),
                    int((max(y_coords) - min(y_coords)) * h)
                )
                
                results.append(FaceLandmarkerResult(
                    landmarks=landmarks,
                    blendshapes=blendshapes,
                    face_bbox=bbox,
                    confidence=0.9  # MediaPipe는 신뢰도를 직접 제공하지 않음
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Face landmark detection error: {e}")
            raise FaceDetectionError(
                ErrorCode.INTERNAL_ERROR,
                f"얼굴 랜드마크 감지 중 오류: {str(e)}"
            )
    
    def _detect_fallback(self, image: np.ndarray) -> List[FaceLandmarkerResult]:
        """
        MediaPipe 사용 불가 시 대체 감지
        OpenCV Haar Cascade 사용
        """
        import cv2
        
        # Haar Cascade로 얼굴 감지
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        results = []
        for (x, y, w, h) in faces:
            results.append(FaceLandmarkerResult(
                landmarks=[],  # Haar Cascade는 랜드마크 없음
                blendshapes={},  # 블렌드쉐이프 없음
                face_bbox=(x, y, w, h),
                confidence=0.7
            ))
        
        return results
    
    def get_blendshapes(self, image: np.ndarray) -> Optional[Dict[str, float]]:
        """
        첫 번째 감지된 얼굴의 블렌드쉐이프 반환
        """
        results = self.detect(image)
        if not results:
            return None
        return results[0].blendshapes


# 싱글톤 인스턴스
_landmarker_instance: Optional[MediaPipeLandmarker] = None


def get_landmarker() -> MediaPipeLandmarker:
    """랜드마커 인스턴스 반환"""
    global _landmarker_instance
    if _landmarker_instance is None:
        _landmarker_instance = MediaPipeLandmarker()
    return _landmarker_instance
