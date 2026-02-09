"""
결과 저장소 인터페이스 (Port)

[Repository Pattern]
이 인터페이스를 구현하면 다양한 저장소로 교체 가능:
- NullRepository: 아무것도 저장하지 않음 (현재)
- FirebaseRepository: Firestore에 저장
- PostgresRepository: PostgreSQL에 저장
- FileLogRepository: 로컬 파일에 로그로 저장
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.result_models import AnalysisResult


class IResultRepository(ABC):
    """분석 결과 저장소 인터페이스"""
    
    @abstractmethod
    async def save(self, result: "AnalysisResult") -> bool:
        """
        분석 결과 저장
        
        Args:
            result: 분석 결과 객체
            
        Returns:
            저장 성공 여부
        """
        pass
