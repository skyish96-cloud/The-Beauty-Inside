"""
연예인 메타/임베딩 로드 모듈
메모리 캐시 지원
"""
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.core.config import settings
from app.core.logger import get_logger
from app.infra.celeb_store.paths import celeb_paths

logger = get_logger(__name__)


@dataclass
class CelebInfo:
    """연예인 정보"""
    celeb_id: str
    name: str
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    agency: Optional[str] = None
    
    @classmethod
    def from_csv_row(cls, row: dict) -> "CelebInfo":
        return cls(
            celeb_id=row.get("celeb_id", ""),
            name=row.get("name", ""),
            gender=row.get("gender"),
            birth_year=int(row["birth_year"]) if row.get("birth_year") else None,
            agency=row.get("agency"),
        )


@dataclass
class CelebImageInfo:
    """연예인 이미지 정보"""
    celeb_id: str
    expression: str
    image_path: str
    embedding_index: Optional[int] = None


class CelebDataLoader:
    """연예인 데이터 로더 (싱글톤 패턴)"""
    
    _instance: Optional["CelebDataLoader"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "CelebDataLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._celebs: Dict[str, CelebInfo] = {}
        self._embeddings: Optional[np.ndarray] = None
        self._ids: Optional[np.ndarray] = None
        self._id_to_index: Dict[str, int] = {}
        self._loaded = False
        self._initialized = True
    
    def load(self) -> None:
        """데이터 로드"""
        if self._loaded:
            logger.info("Data already loaded, skipping")
            return
        
        logger.info("Loading celebrity data...")
        
        # 경로 유효성 검사
        if not celeb_paths.is_valid():
            missing = [k for k, v in celeb_paths.validate().items() if not v]
            logger.warning(f"Missing data files: {missing}")
        
        # 메타 데이터 로드
        self._load_celebs_meta()
        
        # 임베딩 로드
        self._load_embeddings()
        
        self._loaded = True
        logger.info(f"Loaded {len(self._celebs)} celebrities, {len(self._embeddings) if self._embeddings is not None else 0} embeddings")
    
    def _load_celebs_meta(self) -> None:
        """연예인 메타 데이터 로드"""
        csv_path = celeb_paths.celebs_csv
        if not csv_path.exists():
            logger.warning(f"Celebs CSV not found: {csv_path}")
            return
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                celeb = CelebInfo.from_csv_row(row)
                self._celebs[celeb.celeb_id] = celeb
    
    def _load_embeddings(self) -> None:
        """임베딩 데이터 로드"""
        embeddings_path = celeb_paths.embeddings_npy
        ids_path = celeb_paths.ids_npy
        
        if not embeddings_path.exists():
            logger.warning(f"Embeddings not found: {embeddings_path}")
            return
        
        self._embeddings = np.load(str(embeddings_path))
        
        if ids_path.exists():
            self._ids = np.load(str(ids_path), allow_pickle=True)
            # ID to index 매핑 생성
            for idx, id_val in enumerate(self._ids):
                self._id_to_index[str(id_val)] = idx
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    @property
    def celebs(self) -> Dict[str, CelebInfo]:
        """연예인 정보 딕셔너리"""
        return self._celebs
    
    @property
    def embeddings(self) -> Optional[np.ndarray]:
        """임베딩 배열"""
        return self._embeddings
    
    @property
    def ids(self) -> Optional[np.ndarray]:
        """ID 배열"""
        return self._ids
    
    def get_celeb(self, celeb_id: str) -> Optional[CelebInfo]:
        """연예인 정보 조회"""
        return self._celebs.get(celeb_id)
    
    def get_celeb_name(self, celeb_id: str) -> str:
        """연예인 이름 조회"""
        celeb = self.get_celeb(celeb_id)
        return celeb.name if celeb else celeb_id
    
    def get_embedding(self, celeb_id: str) -> Optional[np.ndarray]:
        """특정 연예인의 임베딩 조회"""
        if self._embeddings is None or celeb_id not in self._id_to_index:
            return None
        idx = self._id_to_index[celeb_id]
        return self._embeddings[idx]
    
    def get_all_embeddings(self) -> tuple[np.ndarray, np.ndarray]:
        """모든 임베딩과 ID 반환"""
        if self._embeddings is None or self._ids is None:
            raise ValueError("Embeddings not loaded")
        return self._embeddings, self._ids


# 전역 로더 인스턴스
celeb_loader = CelebDataLoader()


@lru_cache(maxsize=1)
def get_celeb_loader() -> CelebDataLoader:
    """캐시된 로더 인스턴스 반환 (초기화 포함)"""
    loader = CelebDataLoader()
    if not loader.is_loaded:
        loader.load()
    return loader
