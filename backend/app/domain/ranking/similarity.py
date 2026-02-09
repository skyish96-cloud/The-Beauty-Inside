"""
유사도 계산 모듈
cosine/거리 계산 (NumPy/SciPy)
"""
from app.core.debug_tools import trace, trace_enabled, brief

from typing import List, Tuple, Optional

import numpy as np
from scipy.spatial.distance import cosine, euclidean

from app.core.logger import get_logger
from app.utils.timeit import timeit

logger = get_logger(__name__)



if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    코사인 유사도 계산
    
    Args:
        vec1: 첫 번째 벡터
        vec2: 두 번째 벡터
    
    Returns:
        유사도 (0~1, 1이 가장 유사)
    """
    # scipy.cosine은 거리를 반환하므로 1에서 빼기
    return 1 - cosine(vec1, vec2)


def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    유클리드 거리 계산
    
    Args:
        vec1: 첫 번째 벡터
        vec2: 두 번째 벡터
    
    Returns:
        거리 (낮을수록 유사)
    """
    return euclidean(vec1, vec2)


def batch_cosine_similarity(
    query: np.ndarray,
    candidates: np.ndarray
) -> np.ndarray:
    """
    배치 코사인 유사도 계산 (벡터화)
    
    Args:
        query: 쿼리 벡터 (1D 또는 2D)
        candidates: 후보 벡터들 (2D: n_candidates x dim)
    
    Returns:
        유사도 배열 (n_candidates,)
    """
    # 쿼리가 1D면 2D로 변환
    if query.ndim == 1:
        query = query.reshape(1, -1)
    
    # L2 정규화
    query_norm = query / np.linalg.norm(query, axis=1, keepdims=True)
    candidates_norm = candidates / np.linalg.norm(candidates, axis=1, keepdims=True)
    
    # 코사인 유사도 = 정규화된 벡터의 내적
    similarities = np.dot(query_norm, candidates_norm.T).flatten()
    
    return similarities


def batch_euclidean_distance(
    query: np.ndarray,
    candidates: np.ndarray
) -> np.ndarray:
    """
    배치 유클리드 거리 계산 (벡터화)
    
    Args:
        query: 쿼리 벡터 (1D)
        candidates: 후보 벡터들 (2D: n_candidates x dim)
    
    Returns:
        거리 배열 (n_candidates,)
    """
    if query.ndim == 1:
        query = query.reshape(1, -1)
    
    # 브로드캐스팅을 이용한 거리 계산
    diff = candidates - query
    distances = np.linalg.norm(diff, axis=1)
    
    return distances


@trace("compute_similarities")
@timeit("compute_similarities")
def compute_similarities(
    user_embedding: np.ndarray,
    celeb_embeddings: np.ndarray,
    celeb_ids: np.ndarray,
    method: str = "cosine"
) -> List[Tuple[str, float]]:
    """
    사용자 임베딩과 연예인 임베딩 간 유사도 계산
    
    Args:
        user_embedding: 사용자 얼굴 임베딩
        celeb_embeddings: 연예인 임베딩 배열
        celeb_ids: 연예인 ID 배열
        method: 유사도 계산 방법 (cosine, euclidean)
    
    Returns:
        (celeb_id, similarity) 튜플 리스트 (유사도 내림차순 정렬)
    """
    # 입력 검증/진단 로그
    try:
        logger.info("Similarity input validation", data={"user": brief(user_embedding), "candidates": brief(celeb_embeddings), "ids_len": len(celeb_ids)})
    except Exception:
        pass
    if celeb_embeddings is None or len(celeb_ids) == 0:
        raise ValueError("No candidate embeddings")
    if getattr(celeb_embeddings, "ndim", 0) != 2:
        raise ValueError("Candidate embeddings must be 2D")
    if user_embedding is None:
        raise ValueError("User embedding is None")
    if user_embedding.shape[-1] != celeb_embeddings.shape[-1]:
        raise ValueError(f"Embedding dim mismatch: user={user_embedding.shape} cand={celeb_embeddings.shape}")

    if method == "cosine":
        similarities = batch_cosine_similarity(user_embedding, celeb_embeddings)
    elif method == "euclidean":
        # 거리를 유사도로 변환 (작을수록 유사 → 클수록 유사)
        distances = batch_euclidean_distance(user_embedding, celeb_embeddings)
        # 거리를 0-1 유사도로 변환
        max_dist = np.max(distances)
        similarities = 1 - (distances / max_dist) if max_dist > 0 else np.ones_like(distances)
    else:
        raise ValueError(f"Unknown similarity method: {method}")
    
    # (id, similarity) 튜플 생성 및 정렬
    results = [
        (str(celeb_ids[i]), float(similarities[i]))
        for i in range(len(celeb_ids))
    ]
    
    # 유사도 내림차순 정렬
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results


def filter_by_threshold(
    results: List[Tuple[str, float]],
    threshold: float
) -> List[Tuple[str, float]]:
    """
    임계값 이하 결과 필터링
    
    Args:
        results: (id, similarity) 튜플 리스트
        threshold: 최소 유사도 임계값
    
    Returns:
        필터링된 결과 리스트
    """
    return [(id, sim) for id, sim in results if sim >= threshold]


class SimilarityCalculator:
    """유사도 계산기 클래스"""
    
    def __init__(self, method: str = "cosine"):
        """
        Args:
            method: 유사도 계산 방법 (cosine, euclidean)
        """
        self.method = method
    
    def calculate(
        self,
        query: np.ndarray,
        candidates: np.ndarray,
        candidate_ids: np.ndarray
    ) -> List[Tuple[str, float]]:
        """
        유사도 계산
        
        Args:
            query: 쿼리 임베딩
            candidates: 후보 임베딩들
            candidate_ids: 후보 ID들
        
        Returns:
            정렬된 (id, similarity) 리스트
        """
        return compute_similarities(
            query, candidates, candidate_ids, self.method
        )
    
    def get_top_k(
        self,
        query: np.ndarray,
        candidates: np.ndarray,
        candidate_ids: np.ndarray,
        k: int = 3,
        threshold: Optional[float] = None
    ) -> List[Tuple[str, float]]:
        """
        Top-K 유사 후보 반환
        
        Args:
            query: 쿼리 임베딩
            candidates: 후보 임베딩들
            candidate_ids: 후보 ID들
            k: 반환할 개수
            threshold: 최소 유사도 임계값
        
        Returns:
            Top-K (id, similarity) 리스트
        """
        results = self.calculate(query, candidates, candidate_ids)
        
        if threshold is not None:
            results = filter_by_threshold(results, threshold)
        
        return results[:k]
