"""
분석 파이프라인 오케스트레이션 모듈
Step1~4 핵심 파이프라인
"""
from dataclasses import dataclass
from typing import Callable, Optional, List

import numpy as np

from app.core.config import settings
from app.core.errors import ErrorCode, BeautyInsideError, FaceDetectionError
from app.core.logger import get_logger
from app.domain.embedding.deepface_embedder import get_embedder
from app.domain.embedding.face_crop import FaceCropper
from app.domain.expression.expression_map import detect_expression, get_dominant_expression
from app.domain.expression.mp_landmarker import get_landmarker
from app.domain.expression.quality_gate import QualityGate, check_image_quality, validate_face_count
from app.domain.ranking.similarity import SimilarityCalculator
from app.domain.ranking.topk import get_top_k_matches
from app.infra.celeb_store.index import get_expression_index
from app.infra.celeb_store.loader import get_celeb_loader
from app.infra.images.decode import decode_base64_image, bgr_to_rgb
from app.schemas.result_models import (
    AnalysisResult,
    Expression,
    QualityResult,
    RankingResult,
)
from app.schemas.ws_messages import AnalyzeStep
from app.utils.ids import get_or_create_session_id
from app.utils.timeit import StepTimer

logger = get_logger(__name__)


# 진행 상태 콜백 타입
ProgressCallback = Callable[[AnalyzeStep, int, str], None]


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    strict_quality: bool = False  # 품질 문제 시 에러 발생
    filter_by_expression: bool = True  # 표정별 필터링 사용
    fallback_expression: str = "neutral"  # 표정 감지 실패 시 기본값


class AnalyzePipeline:
    """
    얼굴 분석 파이프라인
    
    Step 1: 이미지 디코딩 및 품질 검사
    Step 2: 얼굴 감지 및 표정 분석
    Step 3: 임베딩 추출
    Step 4: 유사도 계산 및 Top-K 선정
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Args:
            config: 파이프라인 설정
        """
        self.config = config or PipelineConfig()
        
        # 컴포넌트 초기화
        self.landmarker = get_landmarker()
        self.embedder = get_embedder()
        self.cropper = FaceCropper()
        self.quality_gate = QualityGate(strict=self.config.strict_quality)
        self.similarity_calc = SimilarityCalculator()
        
        # 데이터 로더
        self._celeb_loader = None
        self._expression_index = None
    
    def _ensure_data_loaded(self):
        """데이터 로딩 확인"""
        if self._celeb_loader is None:
            self._celeb_loader = get_celeb_loader()
        if self._expression_index is None:
            self._expression_index = get_expression_index()
    
    async def analyze(
        self,
        image_data: str,
        session_id: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> AnalysisResult:
        """
        전체 분석 파이프라인 실행
        
        Args:
            image_data: Base64 인코딩된 이미지
            session_id: 세션 ID (None이면 생성)
            progress_callback: 진행 상태 콜백
        
        Returns:
            분석 결과
        
        Raises:
            BeautyInsideError: 분석 실패 시
        """
        timer = StepTimer().start()
        session_id = get_or_create_session_id(session_id)
        log = logger.with_session(session_id)
        
        self._ensure_data_loaded()
        
        try:
            # ========== Step 1: 이미지 디코딩 ==========
            self._notify_progress(progress_callback, AnalyzeStep.RECEIVED, 10, "이미지 수신 완료")
            timer.step("decode")
            
            log.info("Step 1: Decoding image")
            image_bgr = decode_base64_image(image_data)
            image_rgb = bgr_to_rgb(image_bgr)
            
            # ========== Step 2: 얼굴 감지 및 표정 분석 ==========
            self._notify_progress(progress_callback, AnalyzeStep.FACE_DETECTED, 25, "얼굴 감지 중...")
            timer.step("face_detection")
            
            log.info("Step 2: Face detection and expression analysis")
            face_results = self.landmarker.detect(image_rgb)
            
            # 얼굴 수 검증
            validate_face_count(len(face_results))
            
            face_result = face_results[0]
            face_bbox = face_result.face_bbox
            blendshapes = face_result.blendshapes
            
            # 품질 검사
            quality = self.quality_gate.check(
                image_bgr, face_bbox, len(face_results)
            )
            
            # 표정 분석
            self._notify_progress(progress_callback, AnalyzeStep.EXPRESSION_ANALYZED, 40, "표정 분석 중...")
            timer.step("expression")
            
            if blendshapes:
                expression, expr_confidence = get_dominant_expression(blendshapes)
            else:
                expression = Expression.NEUTRAL
                expr_confidence = 0.5
                log.warning("No blendshapes available, using default expression")
            
            log.info(f"Detected expression: {expression.value} (confidence: {expr_confidence:.2f})")
            
            # ========== Step 3: 임베딩 추출 ==========
            self._notify_progress(progress_callback, AnalyzeStep.EMBEDDING_EXTRACTED, 60, "얼굴 특징 추출 중...")
            timer.step("embedding")
            
            log.info("Step 3: Extracting face embedding")
            
            # 얼굴 크롭
            face_image = self.cropper.crop(
                image_rgb,
                face_bbox,
                face_result.landmarks
            )
            
            # 임베딩 추출
            user_embedding = self.embedder.extract(face_image, enforce_detection=False)
            
            # ========== Step 4: 유사도 계산 및 Top-K 선정 ==========
            self._notify_progress(progress_callback, AnalyzeStep.MATCHING, 80, "닮은 연예인 찾는 중...")
            timer.step("matching")
            
            log.info("Step 4: Computing similarity and ranking")
            
            # 연예인 임베딩 가져오기
            celeb_embeddings, celeb_ids = self._celeb_loader.get_all_embeddings()
            
            # 표정별 필터링
            if self.config.filter_by_expression and self._expression_index.has_expression(expression.value):
                celeb_embeddings, celeb_ids = self._expression_index.get_filtered_embeddings(
                    expression.value, celeb_embeddings, celeb_ids
                )
                log.debug(f"Filtered to {len(celeb_ids)} candidates for expression: {expression.value}")
            
            # 유사도 계산
            similarities = self.similarity_calc.calculate(
                user_embedding, celeb_embeddings, celeb_ids
            )
            
            # Top-K 선정
            top_matches = get_top_k_matches(similarities, expression.value)
            
            # ========== 완료 ==========
            timer.stop()
            self._notify_progress(progress_callback, AnalyzeStep.COMPLETED, 100, "분석 완료!")
            
            result = AnalysisResult(
                session_id=session_id,
                detected_expression=expression,
                expression_confidence=expr_confidence,
                top_matches=top_matches,
                quality=quality,
                analysis_time_ms=int(timer.total_ms),
            )
            
            log.info(
                f"Analysis completed: {len(top_matches)} matches found",
                latency_ms=timer.total_ms,
                data={"steps": timer.steps}
            )
            
            return result
            
        except BeautyInsideError:
            raise
        except Exception as e:
            log.exception(f"Pipeline error: {e}")
            raise BeautyInsideError(
                ErrorCode.INTERNAL_ERROR,
                f"분석 중 오류가 발생했습니다: {str(e)}"
            )
    
    def _notify_progress(
        self,
        callback: Optional[ProgressCallback],
        step: AnalyzeStep,
        percent: int,
        message: str
    ):
        """진행 상태 알림"""
        if callback:
            try:
                callback(step, percent, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")


# 전역 파이프라인 인스턴스
_pipeline: Optional[AnalyzePipeline] = None


def get_pipeline() -> AnalyzePipeline:
    """파이프라인 인스턴스 반환"""
    global _pipeline
    if _pipeline is None:
        _pipeline = AnalyzePipeline()
    return _pipeline


async def run_analysis(
    image_data: str,
    session_id: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None
) -> AnalysisResult:
    """
    분석 실행 (헬퍼 함수)
    
    Args:
        image_data: Base64 인코딩된 이미지
        session_id: 세션 ID
        progress_callback: 진행 상태 콜백
    
    Returns:
        분석 결과
    """
    pipeline = get_pipeline()
    return await pipeline.analyze(image_data, session_id, progress_callback)
