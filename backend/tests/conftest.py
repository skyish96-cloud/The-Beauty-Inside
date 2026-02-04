"""
pytest 설정 파일
"""
import sys
from pathlib import Path

# backend 디렉토리를 Python 경로에 추가
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import pytest


@pytest.fixture
def sample_blendshapes():
    """샘플 블렌드쉐이프 데이터"""
    return {
        "mouthSmileLeft": 0.8,
        "mouthSmileRight": 0.75,
        "cheekSquintLeft": 0.5,
        "cheekSquintRight": 0.45,
        "eyeSquintLeft": 0.3,
        "eyeSquintRight": 0.25,
    }


@pytest.fixture
def sample_embedding():
    """샘플 임베딩 벡터"""
    import numpy as np
    np.random.seed(42)
    return np.random.randn(512).astype(np.float32)


@pytest.fixture
def sample_image():
    """샘플 RGB 이미지"""
    import numpy as np
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
