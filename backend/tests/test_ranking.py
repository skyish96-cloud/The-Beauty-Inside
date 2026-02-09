"""
유사도/TopK 테스트
"""
from app.core.debug_tools import trace, trace_enabled, brief

import numpy as np
import pytest

from app.domain.ranking.similarity import (
    SimilarityCalculator,
    batch_cosine_similarity,
    batch_euclidean_distance,
    compute_similarities,
    cosine_similarity,
    euclidean_distance,
    filter_by_threshold,
)
from app.domain.ranking.score_scale import (
    ScoreScaler,
    linear_scale,
    power_scale,
    scale_similarity_to_score,
    sigmoid_scale,
)
from app.domain.ranking.topk import (
    TopKConfig,
    TopKSelector,
    apply_diversity,
    select_top_k,
)
from app.schemas.result_models import Rank


class TestCosineSimilarity:
    """코사인 유사도 테스트"""
    
    def test_identical_vectors(self):
        """동일 벡터는 유사도 1"""
        vec = np.array([1.0, 2.0, 3.0])
        sim = cosine_similarity(vec, vec)
        assert sim == pytest.approx(1.0, abs=0.001)
    
    def test_orthogonal_vectors(self):
        """직교 벡터는 유사도 0"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        sim = cosine_similarity(vec1, vec2)
        assert sim == pytest.approx(0.0, abs=0.001)
    
    def test_opposite_vectors(self):
        """반대 벡터는 유사도 -1"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        sim = cosine_similarity(vec1, vec2)
        assert sim == pytest.approx(-1.0, abs=0.001)


class TestBatchCosineSimilarity:
    """배치 코사인 유사도 테스트"""
    
    def test_single_query_multiple_candidates(self):
        """단일 쿼리, 다중 후보"""
        query = np.array([1.0, 0.0, 0.0])
        candidates = np.array([
            [1.0, 0.0, 0.0],  # 동일
            [0.0, 1.0, 0.0],  # 직교
            [0.5, 0.5, 0.0],  # 유사
        ])
        
        similarities = batch_cosine_similarity(query, candidates)
        
        assert len(similarities) == 3
        assert similarities[0] == pytest.approx(1.0, abs=0.001)
        assert similarities[1] == pytest.approx(0.0, abs=0.001)
        assert 0 < similarities[2] < 1


class TestEuclideanDistance:
    """유클리드 거리 테스트"""
    
    def test_identical_vectors(self):
        """동일 벡터는 거리 0"""
        vec = np.array([1.0, 2.0, 3.0])
        dist = euclidean_distance(vec, vec)
        assert dist == pytest.approx(0.0, abs=0.001)
    
    def test_known_distance(self):
        """알려진 거리"""
        vec1 = np.array([0.0, 0.0])
        vec2 = np.array([3.0, 4.0])
        dist = euclidean_distance(vec1, vec2)
        assert dist == pytest.approx(5.0, abs=0.001)


class TestComputeSimilarities:
    """유사도 계산 테스트"""
    
    def test_sorted_by_similarity(self):
        """유사도 내림차순 정렬"""
        query = np.array([1.0, 0.0, 0.0])
        candidates = np.array([
            [0.5, 0.5, 0.0],  # 중간
            [1.0, 0.0, 0.0],  # 가장 유사
            [0.0, 1.0, 0.0],  # 가장 다름
        ])
        ids = np.array(["A", "B", "C"])
        
        results = compute_similarities(query, candidates, ids)
        
        # B가 가장 유사하므로 첫 번째
        assert results[0][0] == "B"
        # C가 가장 다르므로 마지막
        assert results[-1][0] == "C"


class TestFilterByThreshold:
    """임계값 필터링 테스트"""
    
    def test_filter_low_similarities(self):
        """낮은 유사도 필터링"""
        results = [("A", 0.9), ("B", 0.7), ("C", 0.3), ("D", 0.1)]
        
        filtered = filter_by_threshold(results, 0.5)
        
        assert len(filtered) == 2
        assert filtered[0][0] == "A"
        assert filtered[1][0] == "B"


class TestSimilarityCalculator:
    """SimilarityCalculator 클래스 테스트"""
    
    def test_get_top_k(self):
        """Top-K 반환"""
        calc = SimilarityCalculator()
        query = np.array([1.0, 0.0, 0.0])
        candidates = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.5, 0.5, 0.0],
            [0.0, 1.0, 0.0],
        ])
        ids = np.array(["A", "B", "C", "D"])
        
        top_k = calc.get_top_k(query, candidates, ids, k=2)
        
        assert len(top_k) == 2
        assert top_k[0][0] == "A"


class TestLinearScale:
    """선형 스케일링 테스트"""
    
    def test_min_similarity(self):
        """최소 유사도"""
        score = linear_scale(0.0, min_score=50, max_score=100)
        assert score == 50
    
    def test_max_similarity(self):
        """최대 유사도"""
        score = linear_scale(1.0, min_score=50, max_score=100)
        assert score == 100
    
    def test_mid_similarity(self):
        """중간 유사도"""
        score = linear_scale(0.5, min_score=50, max_score=100)
        assert score == 75


class TestPowerScale:
    """거듭제곱 스케일링 테스트"""
    
    def test_power_less_than_one(self):
        """지수 < 1: 낮은 유사도 부스트"""
        score_linear = linear_scale(0.3, 50, 100)
        score_power = power_scale(0.3, power=0.5, min_score=50, max_score=100)
        
        # 거듭제곱 스케일이 더 높아야 함
        assert score_power > score_linear


class TestSigmoidScale:
    """시그모이드 스케일링 테스트"""
    
    def test_center_point(self):
        """중심점에서의 값"""
        score = sigmoid_scale(0.5, center=0.5, min_score=50, max_score=100)
        # 중심점에서는 중간값
        assert 70 <= score <= 80


class TestScoreScaler:
    """ScoreScaler 클래스 테스트"""
    
    def test_batch_scaling(self):
        """배치 스케일링"""
        scaler = ScoreScaler(method="linear")
        similarities = [0.0, 0.5, 1.0]
        
        scores = scaler.scale_batch(similarities)
        
        assert len(scores) == 3
        assert scores[0] < scores[1] < scores[2]


class TestApplyDiversity:
    """다양성 적용 테스트"""
    
    def test_no_duplicates(self):
        """중복 없는 경우"""
        similarities = [("A", 0.9), ("B", 0.8), ("C", 0.7)]
        
        result = apply_diversity(similarities)
        
        # 순서 유지
        assert result[0][0] == "A"
    
    def test_with_duplicates(self):
        """중복 있는 경우"""
        similarities = [("A", 0.9), ("A", 0.85), ("B", 0.8)]
        
        result = apply_diversity(similarities, penalty=0.2, same_celeb_limit=1)
        
        # 두 번째 A는 패널티 받음
        assert result[0][0] == "A"
        # B가 두 번째 A보다 높아질 수 있음


class TestTopKSelector:
    """TopKSelector 클래스 테스트"""
    
    def test_config_applied(self):
        """설정 적용"""
        config = TopKConfig(k=2, min_similarity=0.5)
        selector = TopKSelector(config)
        
        assert selector.config.k == 2
        assert selector.config.min_similarity == 0.5
    
    def test_get_rank_name(self):
        """순위 이름 반환"""
        selector = TopKSelector()
        
        assert selector.get_rank_name(1) == "금"
        assert selector.get_rank_name(2) == "은"
        assert selector.get_rank_name(3) == "동"
        assert selector.get_rank_name(4) == "4위"
