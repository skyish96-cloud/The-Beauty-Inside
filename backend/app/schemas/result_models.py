"""
결과 모델
Top3/점수/품질플래그 모델
"""
from app.core.debug_tools import trace, trace_enabled, brief

from app.core.logger import get_logger

logger = get_logger(__name__)

if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Rank(str, Enum):
    """순위 등급"""
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"


class Expression(str, Enum):
    """지원 표정 타입"""
    NEUTRAL = "neutral"
    SMILE = "smile"
    SAD = "sad"
    SURPRISE = "surprise"


@dataclass
class FaceInfo:
    """감지된 얼굴 정보"""
    bbox: tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float
    landmarks: Optional[dict] = None


@dataclass
class ExpressionResult:
    """표정 분석 결과"""
    expression: Expression
    confidence: float
    blendshapes: Optional[dict] = None


@dataclass
class QualityResult:
    """이미지 품질 검사 결과"""
    is_valid: bool = True
    is_blurry: bool = False
    is_dark: bool = False
    is_bright: bool = False
    face_size_ok: bool = True
    face_centered: bool = True
    blur_score: float = 0.0
    brightness_score: float = 0.0
    
    @property
    def issues(self) -> List[str]:
        """품질 문제 목록"""
        issues = []
        if self.is_blurry:
            issues.append("blurry")
        if self.is_dark:
            issues.append("dark")
        if self.is_bright:
            issues.append("bright")
        if not self.face_size_ok:
            issues.append("face_too_small")
        if not self.face_centered:
            issues.append("face_not_centered")
        return issues


@dataclass
class CelebCandidate:
    """연예인 후보"""
    celeb_id: str
    name: str
    expression: str
    embedding: Optional[any] = None  # numpy array
    image_path: Optional[str] = None


@dataclass
class SimilarityResult:
    """유사도 계산 결과"""
    celeb_id: str
    name: str
    expression: str
    raw_similarity: float  # 0~1 범위
    scaled_score: float    # 0~100 범위
    image_path: Optional[str] = None


@dataclass
class RankingResult:
    """순위 결과"""
    celeb_id: str
    name: str
    expression: str
    score: float
    rank: Rank
    image_url: Optional[str] = None


@dataclass
class AnalysisResult:
    """전체 분석 결과"""
    session_id: str
    detected_expression: Expression
    expression_confidence: float
    top_matches: List[RankingResult]
    quality: QualityResult
    analysis_time_ms: int
    user_embedding: Optional[any] = None  # 저장하지 않음 (프라이버시)
    
    @trace("AnalysisResult.to_response_dict")
    def to_response_dict(self) -> dict:
        """API 응답용 딕셔너리로 변환"""
        try:
            # top_matches 길이 등 기본 정보만 로그
            if trace_enabled():
                logger.info("AnalysisResult.to_response_dict", data={"session_id": self.session_id, "matches": len(self.top_matches)})
        except Exception:
            pass

        return {
            "session_id": self.session_id,
            "detected_expression": self.detected_expression.value,
            "expression_confidence": self.expression_confidence,
            "matches": [
                {
                    "celeb_id": match.celeb_id,
                    "name": match.name,
                    "similarity_score": match.score,
                    "rank": i + 1,
                    "expression": match.expression,
                    "image_url": match.image_url
                }
                for i, match in enumerate(self.top_matches)
            ],
            "quality_flags": {
                "is_blurry": self.quality.is_blurry,
                "is_dark": self.quality.is_dark,
                "is_bright": self.quality.is_bright,
                "face_size_ok": self.quality.face_size_ok,
                "face_centered": self.quality.face_centered
            },
            "analysis_time_ms": self.analysis_time_ms
        }
