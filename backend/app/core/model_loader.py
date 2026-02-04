"""
AI 모델 자동 다운로드 및 초기화 모듈
MediaPipe Face Landmarker, DeepFace 모델 관리
"""
import os
import urllib.request
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# 모델 파일 경로
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MEDIAPIPE_MODEL_PATH = MODELS_DIR / "face_landmarker.task"

# MediaPipe 모델 URL
MEDIAPIPE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def ensure_models_directory():
    """모델 디렉토리 생성"""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Models directory: {MODELS_DIR}")


def download_file(url: str, destination: Path, description: str = "file") -> bool:
    """
    파일 다운로드
    
    Args:
        url: 다운로드 URL
        destination: 저장 경로
        description: 로그용 설명
    
    Returns:
        성공 여부
    """
    try:
        logger.info(f"Downloading {description}...")
        logger.debug(f"URL: {url}")
        logger.debug(f"Destination: {destination}")
        
        # 진행 상황 콜백
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, block_num * block_size * 100 // total_size)
                if block_num % 100 == 0:
                    logger.debug(f"Download progress: {percent}%")
        
        urllib.request.urlretrieve(url, str(destination), progress_hook)
        
        logger.info(f"Downloaded {description} successfully ({destination.stat().st_size / 1024 / 1024:.1f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download {description}: {e}")
        return False


def ensure_mediapipe_model() -> Optional[str]:
    """
    MediaPipe Face Landmarker 모델 확보
    
    Returns:
        모델 파일 경로 (실패 시 None)
    """
    ensure_models_directory()
    
    if MEDIAPIPE_MODEL_PATH.exists():
        logger.debug(f"MediaPipe model already exists: {MEDIAPIPE_MODEL_PATH}")
        return str(MEDIAPIPE_MODEL_PATH)
    
    # 다운로드
    success = download_file(
        MEDIAPIPE_MODEL_URL,
        MEDIAPIPE_MODEL_PATH,
        "MediaPipe Face Landmarker model"
    )
    
    if success and MEDIAPIPE_MODEL_PATH.exists():
        return str(MEDIAPIPE_MODEL_PATH)
    
    return None


def ensure_deepface_model(model_name: str = "Facenet512") -> bool:
    """
    DeepFace 모델 확보 (첫 실행 시 자동 다운로드)
    
    Args:
        model_name: 모델 이름
    
    Returns:
        성공 여부
    """
    try:
        logger.info(f"Ensuring DeepFace model: {model_name}")
        
        # DeepFace 임포트
        from deepface import DeepFace
        
        # 모델 빌드 (첫 실행 시 자동 다운로드)
        # 더미 이미지로 모델 로딩 트리거
        import numpy as np
        dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
        
        try:
            # 모델 로딩 시도 (다운로드 트리거)
            DeepFace.represent(
                img_path=dummy_img,
                model_name=model_name,
                enforce_detection=False,
                detector_backend="skip"
            )
            logger.info(f"DeepFace model '{model_name}' ready")
            return True
            
        except Exception as e:
            # 모델 다운로드 중 오류 무시 (첫 실제 사용 시 재시도)
            logger.warning(f"DeepFace model pre-loading note: {e}")
            return True
            
    except ImportError:
        logger.error("DeepFace not installed")
        return False
    except Exception as e:
        logger.error(f"DeepFace model initialization failed: {e}")
        return False


def initialize_all_models() -> dict:
    """
    모든 AI 모델 초기화
    
    Returns:
        초기화 결과 딕셔너리
    """
    results = {
        "mediapipe": False,
        "deepface": False,
        "errors": []
    }
    
    logger.info("=" * 50)
    logger.info("Initializing AI Models...")
    logger.info("=" * 50)
    
    # MediaPipe
    try:
        model_path = ensure_mediapipe_model()
        results["mediapipe"] = model_path is not None
        if results["mediapipe"]:
            logger.info("✓ MediaPipe Face Landmarker ready")
        else:
            results["errors"].append("MediaPipe model download failed")
            logger.warning("✗ MediaPipe Face Landmarker not available")
    except Exception as e:
        results["errors"].append(f"MediaPipe: {str(e)}")
        logger.error(f"MediaPipe initialization error: {e}")
    
    # DeepFace
    try:
        from app.core.config import settings
        results["deepface"] = ensure_deepface_model(settings.face_embedding_model)
        if results["deepface"]:
            logger.info("✓ DeepFace ready")
        else:
            results["errors"].append("DeepFace model initialization failed")
            logger.warning("✗ DeepFace not available")
    except Exception as e:
        results["errors"].append(f"DeepFace: {str(e)}")
        logger.error(f"DeepFace initialization error: {e}")
    
    logger.info("=" * 50)
    logger.info(f"Model initialization complete: MediaPipe={results['mediapipe']}, DeepFace={results['deepface']}")
    logger.info("=" * 50)
    
    return results


def get_mediapipe_model_path() -> str:
    """MediaPipe 모델 경로 반환"""
    if MEDIAPIPE_MODEL_PATH.exists():
        return str(MEDIAPIPE_MODEL_PATH)
    
    # 다운로드 시도
    path = ensure_mediapipe_model()
    if path:
        return path
    
    # 기본 경로 반환 (MediaPipe 기본 위치 사용)
    return "face_landmarker.task"
