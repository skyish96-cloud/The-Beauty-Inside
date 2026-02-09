"""
점수 스케일링 모듈
유사도(0~1) → 표시점수(0~100) 변환
"""
from app.core.debug_tools import trace, trace_enabled, brief

from typing import Callable, Optional

import numpy as np

from app.core.logger import get_logger

logger = get_logger(__name__)



if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

# 스케일링 함수 타입
ScaleFunction = Callable[[float], float]


def linear_scale(similarity: float, min_score: float = 50, max_score: float = 99) -> float:
    """
    선형 스케일링
    
    유사도 0~1을 min_score~max_score로 변환
    
    Args:
        similarity: 원본 유사도 (0~1)
        min_score: 최소 출력 점수
        max_score: 최대 출력 점수
    
    Returns:
        변환된 점수
    """
    # 유사도가 음수인 경우 처리
    similarity = max(0.0, min(1.0, similarity))
    
    scaled = min_score + (similarity * (max_score - min_score))
    return round(scaled, 1)


def sigmoid_scale(
    similarity: float,
    center: float = 0.5,
    steepness: float = 10,
    min_score: float = 50,
    max_score: float = 99
) -> float:
    """
    시그모이드 스케일링 (S자 곡선)
    
    중간 유사도 구간에서 더 민감하게 반응
    
    Args:
        similarity: 원본 유사도 (0~1)
        center: 시그모이드 중심점
        steepness: 기울기
        min_score: 최소 출력 점수
        max_score: 최대 출력 점수
    
    Returns:
        변환된 점수
    """
    similarity = max(0.0, min(1.0, similarity))
    
    # 시그모이드 적용
    sigmoid_val = 1 / (1 + np.exp(-steepness * (similarity - center)))
    
    scaled = min_score + (sigmoid_val * (max_score - min_score))
    return round(scaled, 1)


def power_scale(
    similarity: float,
    power: float = 0.5,
    min_score: float = 50,
    max_score: float = 99
) -> float:
    """
    거듭제곱 스케일링
    
    power < 1: 낮은 유사도를 더 높게 표시
    power > 1: 높은 유사도를 더 높게 표시
    
    Args:
        similarity: 원본 유사도 (0~1)
        power: 거듭제곱 지수
        min_score: 최소 출력 점수
        max_score: 최대 출력 점수
    
    Returns:
        변환된 점수
    """
    similarity = max(0.0, min(1.0, similarity))
    
    powered = similarity ** power
    scaled = min_score + (powered * (max_score - min_score))
    
    return round(scaled, 1)


def percentile_scale(
    similarity: float,
    percentile_map: dict,
    min_score: float = 50,
    max_score: float = 99
) -> float:
    """
    백분위 기반 스케일링
    
    사전 정의된 백분위 맵에 따라 변환
    
    Args:
        similarity: 원본 유사도 (0~1)
        percentile_map: {similarity_threshold: percentile_score} 딕셔너리
        min_score: 최소 출력 점수
        max_score: 최대 출력 점수
    
    Returns:
        변환된 점수
    """
    # 임계값 정렬
    thresholds = sorted(percentile_map.keys())
    
    # 해당 구간 찾기
    for i, threshold in enumerate(thresholds):
        if similarity <= threshold:
            if i == 0:
                return min_score
            
            # 선형 보간
            prev_threshold = thresholds[i - 1]
            prev_score = percentile_map[prev_threshold]
            curr_score = percentile_map[threshold]
            
            ratio = (similarity - prev_threshold) / (threshold - prev_threshold)
            return round(prev_score + ratio * (curr_score - prev_score), 1)
    
    return max_score


# 기본 백분위 맵 (유사도 → 표시 점수)
DEFAULT_PERCENTILE_MAP = {
    0.3: 50,   # 30% 유사도 → 50점
    0.5: 70,   # 50% 유사도 → 70점
    0.7: 85,   # 70% 유사도 → 85점
    0.8: 90,   # 80% 유사도 → 90점
    0.9: 95,   # 90% 유사도 → 95점
    1.0: 99,   # 100% 유사도 → 99점
}


class ScoreScaler:
    """점수 스케일러 클래스"""
    
    def __init__(
        self,
        method: str = "linear",
        min_score: float = 50,
        max_score: float = 99,
        **kwargs
    ):
        """
        Args:
            method: 스케일링 방법 (linear, sigmoid, power, percentile)
            min_score: 최소 출력 점수
            max_score: 최대 출력 점수
            **kwargs: 방법별 추가 파라미터
        """
        self.method = method
        self.min_score = min_score
        self.max_score = max_score
        self.kwargs = kwargs
        
        # 스케일링 함수 선택
        self._scale_func = self._get_scale_func()
    
    def _get_scale_func(self) -> ScaleFunction:
        """스케일링 함수 반환"""
        if self.method == "linear":
            return lambda x: linear_scale(x, self.min_score, self.max_score)
        elif self.method == "sigmoid":
            center = self.kwargs.get("center", 0.5)
            steepness = self.kwargs.get("steepness", 10)
            return lambda x: sigmoid_scale(
                x, center, steepness, self.min_score, self.max_score
            )
        elif self.method == "power":
            power = self.kwargs.get("power", 0.5)
            return lambda x: power_scale(
                x, power, self.min_score, self.max_score
            )
        elif self.method == "percentile":
            pmap = self.kwargs.get("percentile_map", DEFAULT_PERCENTILE_MAP)
            return lambda x: percentile_scale(
                x, pmap, self.min_score, self.max_score
            )
        else:
            logger.warning(f"Unknown scale method: {self.method}, using linear")
            return lambda x: linear_scale(x, self.min_score, self.max_score)
    
    def scale(self, similarity: float) -> float:
        """
        유사도를 표시 점수로 변환
        
        Args:
            similarity: 원본 유사도 (0~1)
        
        Returns:
            표시 점수 (min_score~max_score)
        """
        return self._scale_func(similarity)
    
    def scale_batch(self, similarities: list) -> list:
        """
        여러 유사도를 일괄 변환
        
        Args:
            similarities: 유사도 리스트
        
        Returns:
            점수 리스트
        """
        return [self.scale(sim) for sim in similarities]


# 기본 스케일러 인스턴스
default_scaler = ScoreScaler(method="power", power=0.7)


@trace("scale_similarity_to_score")
def scale_similarity_to_score(similarity: float) -> float:
    """기본 스케일러를 사용한 점수 변환"""
    return default_scaler.scale(similarity)
