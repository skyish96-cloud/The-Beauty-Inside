"""
데이터 경로 규약 모듈
하드코딩 금지 - 모든 경로는 여기서 관리
"""
from pathlib import Path
from typing import Optional

from app.core.config import settings


class CelebPaths:
    """연예인 데이터 경로 관리"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.data_dir)
    
    # ================== 메타 데이터 ==================
    
    @property
    def meta_dir(self) -> Path:
        """메타 데이터 디렉토리"""
        return self.base_dir / "celebs" / "meta"
    
    @property
    def celebs_csv(self) -> Path:
        """연예인 목록 CSV (celeb_id, name, gender 등)"""
        return self.meta_dir / "celebs.csv"
    
    @property
    def images_csv(self) -> Path:
        """이미지 메타 CSV (celeb_id, expression, image_path)"""
        return self.meta_dir / "images.csv"
    
    # ================== 임베딩 ==================
    
    @property
    def embeddings_dir(self) -> Path:
        """임베딩 데이터 디렉토리"""
        return self.base_dir / "celebs" / "embeddings"
    
    @property
    def embeddings_npy(self) -> Path:
        """전체 임베딩 NumPy 파일"""
        return self.embeddings_dir / "embed.npy"
    
    @property
    def ids_npy(self) -> Path:
        """임베딩 순서에 대응하는 ID 배열"""
        return self.embeddings_dir / "ids.npy"
    
    @property
    def expression_index_json(self) -> Path:
        """표정별 인덱스 JSON"""
        return self.embeddings_dir / "expr_index.json"
    
    # ================== 이미지 ==================
    
    @property
    def images_dir(self) -> Path:
        """연예인 이미지 디렉토리"""
        return self.base_dir / "celebs" / "images"
    
    def expression_images_dir(self, expression: str) -> Path:
        """특정 표정의 이미지 디렉토리"""
        return self.images_dir / expression
    
    def celeb_image_path(self, expression: str, celeb_id: str, ext: str = "jpg") -> Path:
        """특정 연예인의 특정 표정 이미지 경로"""
        return self.expression_images_dir(expression) / f"{celeb_id}.{ext}"
    
    # ================== 캐시 ==================
    
    @property
    def cache_dir(self) -> Path:
        """캐시 디렉토리"""
        return self.base_dir / "cache"
    
    # ================== 유효성 검사 ==================
    
    def validate(self) -> dict:
        """필수 파일/디렉토리 존재 여부 검사"""
        checks = {
            "meta_dir": self.meta_dir.exists(),
            "celebs_csv": self.celebs_csv.exists(),
            "embeddings_dir": self.embeddings_dir.exists(),
            "embeddings_npy": self.embeddings_npy.exists(),
            "ids_npy": self.ids_npy.exists(),
            "images_dir": self.images_dir.exists(),
        }
        return checks
    
    def is_valid(self) -> bool:
        """모든 필수 파일이 존재하는지 확인"""
        return all(self.validate().values())


# 전역 인스턴스
celeb_paths = CelebPaths()
