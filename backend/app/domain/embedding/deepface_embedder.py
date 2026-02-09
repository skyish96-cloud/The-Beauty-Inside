"""
DeepFace 임베딩 추출 래퍼 모듈
"""
from app.core.debug_tools import trace, trace_enabled, brief

from functools import lru_cache
from typing import Optional, List, Dict, Any

import numpy as np

from app.core.config import settings
from app.core.errors import ErrorCode, FaceDetectionError, SystemError
from app.core.logger import get_logger
from app.utils.timeit import timeit

logger = get_logger(__name__)


if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

# DeepFace 지연 로딩
_deepface = None
_model_initialized = False


@trace("deepface._get_deepface")
def _get_deepface():
    """DeepFace 모듈 지연 로딩"""
    global _deepface, _model_initialized
    
    if _model_initialized:
        return _deepface
    
    try:
        from deepface import DeepFace
        _deepface = DeepFace
        _model_initialized = True
        
        # 모델 사전 로딩 (첫 호출 시 로딩 시간 단축)
        logger.info(f"Loading DeepFace model: {settings.face_embedding_model}")
        
    except Exception as e:
        logger.error(f"DeepFace initialization failed: {e}")
        _model_initialized = True
        _deepface = None
    
    return _deepface


class DeepFaceEmbedder:
    """DeepFace 기반 얼굴 임베딩 추출기"""
    
    def __init__(
        self,
        model_name: str = None,
        detector_backend: str = None
    ):
        """
        Args:
            model_name: 임베딩 모델 (Facenet512, VGG-Face, ArcFace 등)
            detector_backend: 얼굴 감지 백엔드 (retinaface, mtcnn, opencv 등)
        """
        self.model_name = model_name or settings.face_embedding_model
        self.detector_backend = detector_backend or settings.face_detector_backend
        self._deepface = None
    
    def _ensure_initialized(self):
        """초기화 확인"""
        if self._deepface is None:
            self._deepface = _get_deepface()
        
        if self._deepface is None:
            raise SystemError(
                ErrorCode.MODEL_LOAD_ERROR,
                "DeepFace 모델을 로드할 수 없습니다"
            )
    
    @trace("deepface.extract")
    @timeit("extract_embedding")
    def extract(
        self,
        image: np.ndarray,
        enforce_detection: bool = True,
        align: bool = True
    ) -> np.ndarray:
        """
        이미지에서 얼굴 임베딩 추출
        
        Args:
            image: RGB 형식의 NumPy 배열
            enforce_detection: True면 얼굴 미감지 시 에러
            align: 얼굴 정렬 수행 여부
        
        Returns:
            임베딩 벡터 (1D numpy array)
        
        Raises:
            FaceDetectionError: 얼굴 감지 실패
            SystemError: 모델 오류
        """
        self._ensure_initialized()
        try:
            logger.info("DeepFace extract input", data={"model_name": self.model_name, "detector_backend": self.detector_backend, "image": brief(image)})
        except Exception:
            pass

        try:
            # DeepFace.represent()는 리스트 반환
            results = self._deepface.represent(
                img_path=image,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=enforce_detection,
                align=align,
            )
            try:
                logger.info("DeepFace represent result", data={"num_faces": len(results) if results else 0})
            except Exception:
                pass

            if not results:
                raise FaceDetectionError(
                    ErrorCode.NO_FACE_DETECTED,
                    "임베딩 추출을 위한 얼굴을 찾을 수 없습니다"
                )
            
            # 첫 번째 얼굴의 임베딩 반환
            embedding = np.array(results[0]["embedding"])
            
            # L2 정규화
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except ValueError as e:
            if "Face could not be detected" in str(e):
                raise FaceDetectionError(
                    ErrorCode.NO_FACE_DETECTED,
                    "얼굴을 감지할 수 없습니다"
                )
            raise
            
        except Exception as e:
            logger.error(f"Embedding extraction error: {e}")
            raise SystemError(
                ErrorCode.INTERNAL_ERROR,
                f"임베딩 추출 중 오류: {str(e)}"
            )
    
    def extract_multiple(
        self,
        image: np.ndarray,
        max_faces: int = 5
    ) -> List[Dict[str, Any]]:
        """
        이미지에서 여러 얼굴의 임베딩 추출
        
        Args:
            image: RGB 형식의 NumPy 배열
            max_faces: 최대 추출 얼굴 수
        
        Returns:
            얼굴별 임베딩과 메타데이터 리스트
        """
        self._ensure_initialized()
        try:
            logger.info("DeepFace extract input", data={"model_name": self.model_name, "detector_backend": self.detector_backend, "image": brief(image)})
        except Exception:
            pass

        try:
            results = self._deepface.represent(
                img_path=image,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                align=True,
            )
            
            embeddings = []
            for i, result in enumerate(results[:max_faces]):
                embedding = np.array(result["embedding"])
                embedding = embedding / np.linalg.norm(embedding)
                
                embeddings.append({
                    "embedding": embedding,
                    "facial_area": result.get("facial_area", {}),
                    "face_confidence": result.get("face_confidence", 0.0),
                })
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Multiple embedding extraction error: {e}")
            return []
    
    def get_embedding_dim(self) -> int:
        """임베딩 차원 반환"""
        dims = {
            "VGG-Face": 4096,
            "Facenet": 128,
            "Facenet512": 512,
            "OpenFace": 128,
            "DeepFace": 4096,
            "DeepID": 160,
            "ArcFace": 512,
            "Dlib": 128,
            "SFace": 128,
        }
        return dims.get(self.model_name, 512)


# 싱글톤 인스턴스
_embedder_instance: Optional[DeepFaceEmbedder] = None


def get_embedder() -> DeepFaceEmbedder:
    """임베더 인스턴스 반환"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = DeepFaceEmbedder()
    return _embedder_instance
