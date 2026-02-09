"""
Top-K 선정 모듈
gold/silver/bronze 선정 규칙
"""
from app.core.debug_tools import trace, trace_enabled, brief

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from app.core.config import settings
from app.core.logger import get_logger
from app.infra.celeb_store.loader import get_celeb_loader
from app.infra.celeb_store.paths import celeb_paths
from app.schemas.result_models import Rank, RankingResult, SimilarityResult
from app.domain.ranking.score_scale import scale_similarity_to_score

logger = get_logger(__name__)



if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

# 순위별 등급
RANK_NAMES = {
    1: Rank.GOLD,
    2: Rank.SILVER,
    3: Rank.BRONZE,
}


@dataclass
class TopKConfig:
    """Top-K 설정"""
    k: int = 3
    min_similarity: float = 0.4
    diversity_penalty: float = 0.0  # 동일 연예인 중복 방지 패널티
    expression_match_bonus: float = 0.0  # 표정 일치 보너스


@trace("select_top_k")
def select_top_k(
    similarities: List[Tuple[str, float]],
    k: int = None,
    min_similarity: float = None,
    expression: Optional[str] = None
) -> List[SimilarityResult]:
    """
    Top-K 후보 선정
    
    Args:
        similarities: (celeb_id, similarity) 튜플 리스트 (정렬됨)
        k: 선정할 개수 (None이면 설정값 사용)
        min_similarity: 최소 유사도 임계값
        expression: 감지된 표정 (메타데이터용)
    
    Returns:
        Top-K 유사도 결과 리스트
    """
    try:
        logger.info("TopK select input", data={"pairs_len": len(similarities), "k": k, "min_similarity": min_similarity, "expression": expression})
    except Exception:
        pass

    if k is None:
        k = settings.top_k
    if min_similarity is None:
        min_similarity = settings.similarity_threshold
    
    loader = get_celeb_loader()
    results = []
    
    for celeb_id, similarity in similarities:
        if similarity < min_similarity:
            break
        
        if len(results) >= k:
            break
        
        # 연예인 정보 조회
        celeb_name = loader.get_celeb_name(celeb_id)
        
        # 점수 스케일링
        scaled_score = scale_similarity_to_score(similarity)
        
        results.append(SimilarityResult(
            celeb_id=celeb_id,
            name=celeb_name,
            expression=expression or "neutral",
            raw_similarity=similarity,
            scaled_score=scaled_score,
        ))
    
    return results


@trace("create_ranking_results")
def create_ranking_results(
    similarity_results: List[SimilarityResult],
    expression: str
) -> List[RankingResult]:
    """
    유사도 결과를 순위 결과로 변환
    
    Args:
        similarity_results: 유사도 결과 리스트
        expression: 표정
    
    Returns:
        순위 결과 리스트 (gold, silver, bronze)
    """
    rankings = []
    
    for i, result in enumerate(similarity_results[:3]):
        rank = RANK_NAMES.get(i + 1, Rank.BRONZE)
        
        # 이미지 URL 생성 (famous 폴더의 _01.jpg 사용)
        base_id = result.celeb_id.replace("_original", "")
        filename = f"{base_id}_01.jpg"
        image_url = f"/api/celeb-image/{filename}"
        
        rankings.append(RankingResult(
            celeb_id=result.celeb_id,
            name=result.name,
            expression=expression,
            score=result.scaled_score,
            rank=rank,
            image_url=image_url,
        ))
    
    return rankings


def apply_diversity(
    similarities: List[Tuple[str, float]],
    penalty: float = 0.1,
    same_celeb_limit: int = 1
) -> List[Tuple[str, float]]:
    """
    다양성 적용 (동일 연예인 중복 방지)
    
    Args:
        similarities: (celeb_id, similarity) 튜플 리스트
        penalty: 중복 패널티
        same_celeb_limit: 동일 연예인 허용 횟수
    
    Returns:
        다양성이 적용된 결과 리스트
    """
    celeb_counts = {}
    adjusted = []
    
    for celeb_id, similarity in similarities:
        count = celeb_counts.get(celeb_id, 0)
        
        if count >= same_celeb_limit:
            # 초과 시 패널티 적용
            adjusted_sim = similarity - (penalty * (count - same_celeb_limit + 1))
        else:
            adjusted_sim = similarity
        
        adjusted.append((celeb_id, adjusted_sim))
        celeb_counts[celeb_id] = count + 1
    
    # 재정렬
    adjusted.sort(key=lambda x: x[1], reverse=True)
    return adjusted


class TopKSelector:
    """Top-K 선정 클래스"""
    
    def __init__(self, config: Optional[TopKConfig] = None):
        """
        Args:
            config: Top-K 설정
        """
        self.config = config or TopKConfig()
    
    def select(
        self,
        similarities: List[Tuple[str, float]],
        expression: str
    ) -> List[RankingResult]:
        """
        Top-K 선정 및 순위 결과 생성
        
        Args:
            similarities: (celeb_id, similarity) 튜플 리스트
            expression: 감지된 표정
        
        Returns:
            순위 결과 리스트
        """
        # 다양성 적용
        if self.config.diversity_penalty > 0:
            similarities = apply_diversity(
                similarities, self.config.diversity_penalty
            )
        
        # Top-K 선정
        top_results = select_top_k(
            similarities,
            k=self.config.k,
            min_similarity=self.config.min_similarity,
            expression=expression
        )
        
        # 순위 결과 생성
        rankings = create_ranking_results(top_results, expression)
        
        return rankings
    
    def get_rank_name(self, position: int) -> str:
        """
        순위 이름 반환
        
        Args:
            position: 순위 (1-indexed)
        
        Returns:
            순위 이름 (금, 은, 동)
        """
        names = {1: "금", 2: "은", 3: "동"}
        return names.get(position, f"{position}위")


# 기본 셀렉터 인스턴스
default_selector = TopKSelector()


def get_top_k_matches(
    similarities: List[Tuple[str, float]],
    expression: str
) -> List[RankingResult]:
    """기본 셀렉터를 사용한 Top-K 매칭"""
    return default_selector.select(similarities, expression)
