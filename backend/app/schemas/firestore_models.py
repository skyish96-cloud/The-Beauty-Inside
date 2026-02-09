"""
Firestore 저장용 DTO
"""
from app.core.debug_tools import trace, trace_enabled, brief

from app.core.logger import get_logger

logger = get_logger(__name__)

if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class SessionDocument:
    """세션 문서 (sessions 컬렉션)"""
    session_id: str
    created_at: datetime
    client_info: Optional[dict] = None
    status: str = "active"  # active, completed, expired
    
    @trace("SessionDocument.to_dict")
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "client_info": self.client_info,
            "status": self.status
        }


@dataclass
class AnalysisDocument:
    """분석 결과 문서 (analyses 컬렉션)"""
    analysis_id: str
    session_id: str
    created_at: datetime
    detected_expression: str
    expression_confidence: float
    quality_flags: dict
    analysis_time_ms: int
    
    @trace("AnalysisDocument.to_dict")
    def to_dict(self) -> dict:
        return {
            "analysis_id": self.analysis_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "detected_expression": self.detected_expression,
            "expression_confidence": self.expression_confidence,
            "quality_flags": self.quality_flags,
            "analysis_time_ms": self.analysis_time_ms
        }


@dataclass
class MatchResult:
    """매칭 결과 (results 서브컬렉션)"""
    celeb_id: str
    celeb_name: str
    similarity_score: float
    rank: int
    expression: str
    
    @trace("MatchResult.to_dict")
    def to_dict(self) -> dict:
        return {
            "celeb_id": self.celeb_id,
            "celeb_name": self.celeb_name,
            "similarity_score": self.similarity_score,
            "rank": self.rank,
            "expression": self.expression
        }


@dataclass
class ResultDocument:
    """전체 결과 문서 (results 컬렉션)"""
    result_id: str
    analysis_id: str
    session_id: str
    created_at: datetime
    matches: List[MatchResult]
    
    @trace("ResultDocument.to_dict")
    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "analysis_id": self.analysis_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "matches": [m.to_dict() for m in self.matches]
        }


@dataclass
class AggregateStats:
    """집계 통계 (선택적)"""
    total_analyses: int = 0
    expression_counts: dict = None
    top_matched_celebs: dict = None
    avg_analysis_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.expression_counts is None:
            self.expression_counts = {}
        if self.top_matched_celebs is None:
            self.top_matched_celebs = {}
    
    @trace("AggregateStats.to_dict")
    def to_dict(self) -> dict:
        return asdict(self)
