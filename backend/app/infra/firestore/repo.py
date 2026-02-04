"""
Firestore 저장소 모듈
sessions/analyses/results 저장 함수
"""
from datetime import datetime
from typing import Optional

from app.core.logger import get_logger
from app.infra.firestore.client import firestore_manager
from app.schemas.firestore_models import (
    SessionDocument,
    AnalysisDocument,
    ResultDocument,
    MatchResult,
)
from app.schemas.result_models import AnalysisResult

logger = get_logger(__name__)


class AnalysisRepository:
    """분석 결과 저장소"""
    
    COLLECTION_SESSIONS = "sessions"
    COLLECTION_ANALYSES = "analyses"
    COLLECTION_RESULTS = "results"
    
    def __init__(self):
        self._manager = firestore_manager
    
    @property
    def enabled(self) -> bool:
        return self._manager.enabled
    
    async def save_session(self, session: SessionDocument) -> bool:
        """세션 저장"""
        if not self.enabled:
            logger.debug("Firestore disabled, skipping session save")
            return False
        
        try:
            collection = self._manager.collection(self.COLLECTION_SESSIONS)
            if collection is None:
                return False
            
            collection.document(session.session_id).set(session.to_dict())
            logger.info(f"Session saved: {session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    async def save_analysis(self, analysis: AnalysisDocument) -> bool:
        """분석 결과 저장"""
        if not self.enabled:
            logger.debug("Firestore disabled, skipping analysis save")
            return False
        
        try:
            collection = self._manager.collection(self.COLLECTION_ANALYSES)
            if collection is None:
                return False
            
            collection.document(analysis.analysis_id).set(analysis.to_dict())
            logger.info(f"Analysis saved: {analysis.analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            return False
    
    async def save_analysis_log(self, session_id: str, label: str, score: float) -> bool:
        """실시간 분석 로그 저장 (간단한 버전)"""
        if not self.enabled:
            logger.debug("Firestore disabled, skipping analysis log save")
            return False
        
        try:
            collection = self._manager.collection(self.COLLECTION_ANALYSES)
            if collection is None:
                return False
            
            collection.document().set({
                "session_id": session_id,
                "emotion_label": label,
                "emotion_score": score,
                "timestamp": datetime.utcnow()
            })
            logger.info(f"Analysis log saved for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analysis log: {e}")
            return False
    
    async def save_result(self, result: ResultDocument) -> bool:
        """최종 결과 저장"""
        if not self.enabled:
            logger.debug("Firestore disabled, skipping result save")
            return False
        
        try:
            collection = self._manager.collection(self.COLLECTION_RESULTS)
            if collection is None:
                return False
            
            collection.document(result.result_id).set(result.to_dict())
            logger.info(f"Result saved: {result.result_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
            return False
    
    async def save_final_result(self, session_id: str, matches: list) -> bool:
        """최종 결과 저장 (간단한 버전)"""
        if not self.enabled:
            logger.debug("Firestore disabled, skipping final result save")
            return False
        
        try:
            collection = self._manager.collection(self.COLLECTION_RESULTS)
            if collection is None:
                return False
            
            collection.document().set({
                "session_id": session_id,
                "top_matches": matches,
                "created_at": datetime.utcnow()
            })
            logger.info(f"Final result saved for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save final result: {e}")
            return False
    
    async def save_full_result(self, analysis_result: AnalysisResult) -> bool:
        """전체 분석 결과를 한번에 저장"""
        if not self.enabled:
            return False
        
        try:
            from app.utils.ids import generate_analysis_id, generate_result_id
            
            now = datetime.utcnow()
            analysis_id = generate_analysis_id()
            result_id = generate_result_id()
            
            # 분석 문서 저장
            analysis_doc = AnalysisDocument(
                analysis_id=analysis_id,
                session_id=analysis_result.session_id,
                created_at=now,
                detected_expression=analysis_result.detected_expression.value,
                expression_confidence=analysis_result.expression_confidence,
                quality_flags={
                    "is_blurry": analysis_result.quality.is_blurry,
                    "is_dark": analysis_result.quality.is_dark,
                    "is_bright": analysis_result.quality.is_bright,
                    "face_size_ok": analysis_result.quality.face_size_ok,
                    "face_centered": analysis_result.quality.face_centered,
                },
                analysis_time_ms=analysis_result.analysis_time_ms,
            )
            await self.save_analysis(analysis_doc)
            
            # 결과 문서 저장
            matches = [
                MatchResult(
                    celeb_id=m.celeb_id,
                    celeb_name=m.name,
                    similarity_score=m.score,
                    rank=i + 1,
                    expression=m.expression,
                )
                for i, m in enumerate(analysis_result.top_matches)
            ]
            
            result_doc = ResultDocument(
                result_id=result_id,
                analysis_id=analysis_id,
                session_id=analysis_result.session_id,
                created_at=now,
                matches=matches,
            )
            await self.save_result(result_doc)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save full result: {e}")
            return False


# 전역 저장소 인스턴스
analysis_repo = AnalysisRepository()
