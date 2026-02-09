"""
Blendshape → 표정 라벨 매핑/스코어링 모듈
"""
from app.core.debug_tools import trace, trace_enabled, brief

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.result_models import Expression

logger = get_logger(__name__)



if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

# 표정별 관련 블렌드쉐이프 가중치
EXPRESSION_BLENDSHAPES = {
    Expression.SMILE: {
        "mouthSmileLeft": 0.3,
        "mouthSmileRight": 0.3,
        "cheekSquintLeft": 0.15,
        "cheekSquintRight": 0.15,
        "eyeSquintLeft": 0.05,
        "eyeSquintRight": 0.05,
    },
    Expression.SAD: {
        "mouthFrownLeft": 0.25,
        "mouthFrownRight": 0.25,
        "browDownLeft": 0.15,
        "browDownRight": 0.15,
        "browInnerUp": 0.2,
    },
    Expression.SURPRISE: {
        "browOuterUpLeft": 0.2,
        "browOuterUpRight": 0.2,
        "eyeWideLeft": 0.15,
        "eyeWideRight": 0.15,
        "jawOpen": 0.15,
        "mouthOpen": 0.15,
    },
    Expression.NEUTRAL: {
        # Neutral은 다른 표정 점수가 낮을 때
    },
}


# 표정 임계값 (이 값 이상이면 해당 표정으로 판정)
EXPRESSION_THRESHOLDS = {
    Expression.SMILE: 0.3,
    Expression.SAD: 0.25,
    Expression.SURPRISE: 0.35,
    Expression.NEUTRAL: 0.0,  # 기본값
}


@dataclass
class ExpressionScore:
    """표정 점수"""
    expression: Expression
    score: float
    confidence: float
    raw_scores: Dict[Expression, float]


@trace("calculate_expression_score")
def calculate_expression_score(
    blendshapes: Dict[str, float],
    expression: Expression
) -> float:
    """
    특정 표정에 대한 점수 계산
    
    Args:
        blendshapes: 블렌드쉐이프 값 딕셔너리
        expression: 계산할 표정
    
    Returns:
        0~1 범위의 점수
    """
    if expression not in EXPRESSION_BLENDSHAPES:
        return 0.0
    
    weights = EXPRESSION_BLENDSHAPES[expression]
    if not weights:
        return 0.0
    
    total_score = 0.0
    total_weight = 0.0
    
    for bs_name, weight in weights.items():
        if bs_name in blendshapes:
            total_score += blendshapes[bs_name] * weight
            total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return total_score / total_weight


@trace("detect_expression")
def detect_expression(blendshapes: Dict[str, float]) -> ExpressionScore:
    """
    블렌드쉐이프에서 표정 감지
    
    Args:
        blendshapes: 블렌드쉐이프 값 딕셔너리
    
    Returns:
        감지된 표정과 신뢰도
    """
    if not blendshapes:
        try:
            logger.info("Expression detected", data={"detected": str(Expression.NEUTRAL), "confidence": 0.0, "reason": "empty_blendshapes"})
        except Exception:
            pass

        return ExpressionScore(
            expression=Expression.NEUTRAL,
            score=0.0,
            confidence=0.0,
            raw_scores={e: 0.0 for e in Expression}
        )
    
    # 각 표정별 점수 계산
    scores = {}
    for expr in [Expression.SMILE, Expression.SAD, Expression.SURPRISE]:
        scores[expr] = calculate_expression_score(blendshapes, expr)
    
    # 가장 높은 점수의 표정 선택
    max_expr = max(scores, key=scores.get)
    max_score = scores[max_expr]
    
    # 임계값 확인
    threshold = EXPRESSION_THRESHOLDS.get(max_expr, 0.0)
    
    if max_score >= threshold:
        detected = max_expr
        confidence = min(max_score / (threshold + 0.1), 1.0)
    else:
        detected = Expression.NEUTRAL
        confidence = 1.0 - max(scores.values())
    
    scores[Expression.NEUTRAL] = 1.0 - max(scores.values())

    try:
        logger.info("Expression detected final", data={"detected": str(detected), "confidence": confidence, "scores": {str(k): float(v) for k, v in scores.items()}})
    except Exception:
        pass

    return ExpressionScore(
        expression=detected,
        score=max_score if detected != Expression.NEUTRAL else scores[Expression.NEUTRAL],
        confidence=confidence,
        raw_scores=scores
    )


@trace("get_expression_label")
def get_expression_label(expression: Expression) -> str:
    """표정 한글 라벨 반환"""
    labels = {
        Expression.NEUTRAL: "무표정",
        Expression.SMILE: "웃음",
        Expression.SAD: "슬픔",
        Expression.SURPRISE: "놀람",
    }
    return labels.get(expression, "알 수 없음")


@trace("validate_expression")
def validate_expression(expression: str) -> Optional[Expression]:
    """문자열을 Expression enum으로 변환"""
    try:
        return Expression(expression.lower())
    except ValueError:
        return None


def get_dominant_expression(
    blendshapes: Dict[str, float],
    min_confidence: float = None
) -> Tuple[Expression, float]:
    """
    주요 표정과 신뢰도 반환
    
    Args:
        blendshapes: 블렌드쉐이프 값
        min_confidence: 최소 신뢰도 (None이면 설정값 사용)
    
    Returns:
        (표정, 신뢰도) 튜플
    """
    if min_confidence is None:
        min_confidence = settings.expression_confidence_threshold
    
    result = detect_expression(blendshapes)
    
    if result.confidence < min_confidence:
        return Expression.NEUTRAL, result.confidence
    
    return result.expression, result.confidence
