"""
Null Repository 구현체

아무것도 저장하지 않는 구현체.
현재 프로덕션에서 사용 중이며, 나중에 다른 Repository로 교체 가능.
"""
from app.domain.ports.result_repository import IResultRepository

# TYPE_CHECKING으로 순환 import 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.schemas.result_models import AnalysisResult


class NullRepository(IResultRepository):
    """아무것도 저장하지 않는 구현체"""
    
    async def save(self, result: "AnalysisResult") -> bool:
        """저장하지 않고 성공 반환"""
        return True
