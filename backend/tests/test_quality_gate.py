"""
품질 판정 단위 테스트
"""
import numpy as np
import pytest

from app.core.errors import ErrorCode, FaceDetectionError, ImageQualityError
from app.domain.expression.quality_gate import (
    QualityGate,
    calculate_blur_score,
    calculate_brightness,
    check_face_centered,
    check_face_size,
    check_image_quality,
    validate_face_count,
    validate_quality,
)
from app.schemas.result_models import QualityResult


class TestCalculateBlurScore:
    """흐림 점수 계산 테스트"""
    
    def test_sharp_image_high_score(self):
        """선명한 이미지는 높은 점수"""
        # 엣지가 많은 이미지 생성
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[::2, :, :] = 255  # 줄무늬 패턴
        
        score = calculate_blur_score(image)
        assert score > 1000  # 선명한 이미지는 높은 variance
    
    def test_blurry_image_low_score(self):
        """흐린 이미지는 낮은 점수"""
        # 균일한 이미지 (엣지 없음)
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        score = calculate_blur_score(image)
        assert score < 10  # 흐린 이미지는 낮은 variance
    
    def test_grayscale_input(self):
        """그레이스케일 입력 처리"""
        image = np.zeros((100, 100), dtype=np.uint8)
        image[::2, :] = 255
        
        score = calculate_blur_score(image)
        assert score > 0


class TestCalculateBrightness:
    """밝기 계산 테스트"""
    
    def test_dark_image(self):
        """어두운 이미지"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        brightness = calculate_brightness(image)
        assert brightness == 0
    
    def test_bright_image(self):
        """밝은 이미지"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        brightness = calculate_brightness(image)
        assert brightness == 255
    
    def test_medium_brightness(self):
        """중간 밝기"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        brightness = calculate_brightness(image)
        assert 125 <= brightness <= 130


class TestCheckFaceSize:
    """얼굴 크기 검사 테스트"""
    
    def test_large_face_ok(self):
        """충분히 큰 얼굴"""
        bbox = (50, 50, 100, 100)  # 100x100 픽셀
        image_shape = (480, 640)
        
        assert check_face_size(bbox, image_shape, min_size=80) is True
    
    def test_small_face_fail(self):
        """너무 작은 얼굴"""
        bbox = (50, 50, 50, 50)  # 50x50 픽셀
        image_shape = (480, 640)
        
        assert check_face_size(bbox, image_shape, min_size=80) is False
    
    def test_exactly_min_size(self):
        """정확히 최소 크기"""
        bbox = (50, 50, 80, 80)
        image_shape = (480, 640)
        
        assert check_face_size(bbox, image_shape, min_size=80) is True


class TestCheckFaceCentered:
    """얼굴 중앙 검사 테스트"""
    
    def test_centered_face(self):
        """중앙에 있는 얼굴"""
        # 이미지 중앙에 얼굴
        bbox = (220, 140, 200, 200)  # 중앙 근처
        image_shape = (480, 640)
        
        assert check_face_centered(bbox, image_shape) is True
    
    def test_corner_face(self):
        """모서리에 있는 얼굴"""
        bbox = (0, 0, 100, 100)  # 좌상단 모서리
        image_shape = (480, 640)
        
        assert check_face_centered(bbox, image_shape) is False


class TestValidateFaceCount:
    """얼굴 수 검증 테스트"""
    
    def test_one_face_ok(self):
        """한 명 OK"""
        validate_face_count(1)  # 에러 없이 통과
    
    def test_no_face_error(self):
        """얼굴 없음 에러"""
        with pytest.raises(FaceDetectionError) as exc_info:
            validate_face_count(0)
        
        assert exc_info.value.code == ErrorCode.NO_FACE_DETECTED
    
    def test_multiple_faces_error(self):
        """여러 얼굴 에러"""
        with pytest.raises(FaceDetectionError) as exc_info:
            validate_face_count(3)
        
        assert exc_info.value.code == ErrorCode.MULTIPLE_FACES_DETECTED


class TestCheckImageQuality:
    """이미지 품질 검사 테스트"""
    
    def test_good_quality_image(self):
        """좋은 품질 이미지"""
        # 선명하고 적절한 밝기의 이미지
        image = np.ones((480, 640, 3), dtype=np.uint8) * 128
        image[::2, ::2, :] = 200  # 패턴 추가
        
        bbox = (220, 140, 200, 200)
        quality = check_image_quality(image, bbox)
        
        assert quality.face_size_ok is True
        assert quality.face_centered is True
    
    def test_dark_image_detected(self):
        """어두운 이미지 감지"""
        image = np.ones((480, 640, 3), dtype=np.uint8) * 10
        
        quality = check_image_quality(image)
        
        assert quality.is_dark is True
        assert quality.is_valid is False


class TestQualityGate:
    """QualityGate 클래스 테스트"""
    
    def test_non_strict_mode(self):
        """비엄격 모드에서 품질 문제는 경고만"""
        gate = QualityGate(strict=False)
        image = np.ones((480, 640, 3), dtype=np.uint8) * 10  # 어두운 이미지
        
        quality = gate.check(image, (220, 140, 200, 200), 1)
        
        assert quality.is_dark is True
        # 에러는 발생하지 않음
    
    def test_strict_mode_face_count_error(self):
        """엄격 모드에서 얼굴 수 에러"""
        gate = QualityGate(strict=True)
        image = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        with pytest.raises(FaceDetectionError):
            gate.check(image, (220, 140, 200, 200), 0)


class TestValidateQuality:
    """품질 검증 함수 테스트"""
    
    def test_blurry_raises_error(self):
        """흐림 에러"""
        quality = QualityResult(is_blurry=True, blur_score=50)
        
        with pytest.raises(ImageQualityError) as exc_info:
            validate_quality(quality)
        
        assert exc_info.value.code == ErrorCode.IMAGE_TOO_BLURRY
    
    def test_dark_raises_error(self):
        """어두움 에러"""
        quality = QualityResult(is_dark=True, brightness_score=20)
        
        with pytest.raises(ImageQualityError) as exc_info:
            validate_quality(quality)
        
        assert exc_info.value.code == ErrorCode.IMAGE_TOO_DARK
    
    def test_bright_raises_error(self):
        """밝음 에러"""
        quality = QualityResult(is_bright=True, brightness_score=250)
        
        with pytest.raises(ImageQualityError) as exc_info:
            validate_quality(quality)
        
        assert exc_info.value.code == ErrorCode.IMAGE_TOO_BRIGHT
