"""
표정별 후보 인덱스 모듈
표정에 따라 연예인 후보 필터링
"""
import json
from functools import lru_cache
from typing import Dict, List, Optional, Set

import numpy as np

from app.core.config import settings
from app.core.logger import get_logger
from app.infra.celeb_store.paths import celeb_paths
from app.infra.celeb_store.loader import celeb_loader

logger = get_logger(__name__)


class ExpressionIndex:
    """표정별 연예인 인덱스"""
    
    _instance: Optional["ExpressionIndex"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "ExpressionIndex":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 표정 -> 연예인 ID 리스트
        self._expr_to_celebs: Dict[str, List[str]] = {}
        # 표정 -> 임베딩 인덱스 리스트
        self._expr_to_indices: Dict[str, List[int]] = {}
        # 연예인 ID -> 표정 리스트
        self._celeb_to_exprs: Dict[str, List[str]] = {}
        
        self._loaded = False
        self._initialized = True
    
    def load(self) -> None:
        """인덱스 로드"""
        if self._loaded:
            return
        
        logger.info("Loading expression index...")
        
        index_path = celeb_paths.expression_index_json
        if index_path.exists():
            self._load_from_json(index_path)
        else:
            # JSON이 없으면 이미지 디렉토리 구조에서 추론
            self._build_from_directory()
        
        self._loaded = True
        logger.info(f"Expression index loaded: {list(self._expr_to_celebs.keys())}")
    
    def _load_from_json(self, path) -> None:
        """JSON 파일에서 인덱스 로드"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self._expr_to_celebs = data.get("expression_to_celebs", {})
        self._expr_to_indices = data.get("expression_to_indices", {})
        
        # 역방향 인덱스 구성
        for expr, celebs in self._expr_to_celebs.items():
            for celeb_id in celebs:
                if celeb_id not in self._celeb_to_exprs:
                    self._celeb_to_exprs[celeb_id] = []
                self._celeb_to_exprs[celeb_id].append(expr)
    
    def _build_from_directory(self) -> None:
        """디렉토리 구조에서 인덱스 빌드"""
        images_dir = celeb_paths.images_dir
        if not images_dir.exists():
            logger.warning(f"Images directory not found: {images_dir}")
            return
        
        for expr_dir in images_dir.iterdir():
            if not expr_dir.is_dir():
                continue
            
            expression = expr_dir.name
            self._expr_to_celebs[expression] = []
            
            for image_file in expr_dir.iterdir():
                if image_file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    celeb_id = image_file.stem
                    self._expr_to_celebs[expression].append(celeb_id)
                    
                    if celeb_id not in self._celeb_to_exprs:
                        self._celeb_to_exprs[celeb_id] = []
                    self._celeb_to_exprs[celeb_id].append(expression)
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    @property
    def expressions(self) -> List[str]:
        """지원하는 표정 목록"""
        return list(self._expr_to_celebs.keys())
    
    def get_celebs_by_expression(self, expression: str) -> List[str]:
        """특정 표정의 연예인 ID 목록"""
        return self._expr_to_celebs.get(expression, [])
    
    def get_indices_by_expression(self, expression: str) -> List[int]:
        """특정 표정의 임베딩 인덱스 목록"""
        return self._expr_to_indices.get(expression, [])
    
    def get_expressions_by_celeb(self, celeb_id: str) -> List[str]:
        """특정 연예인이 가진 표정 목록"""
        return self._celeb_to_exprs.get(celeb_id, [])
    
    def get_filtered_embeddings(
        self, 
        expression: str, 
        embeddings: np.ndarray, 
        ids: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        특정 표정에 해당하는 임베딩만 필터링
        
        Returns:
            (filtered_embeddings, filtered_ids)
        """
        target_celebs = set(self.get_celebs_by_expression(expression))
        if not target_celebs:
            # 해당 표정이 없으면 전체 반환
            return embeddings, ids
        
        mask = np.array([str(id_val) in target_celebs for id_val in ids])
        return embeddings[mask], ids[mask]
    
    def has_expression(self, expression: str) -> bool:
        """해당 표정이 있는지 확인"""
        return expression in self._expr_to_celebs
    
    def count_by_expression(self, expression: str) -> int:
        """특정 표정의 연예인 수"""
        return len(self._expr_to_celebs.get(expression, []))


# 전역 인스턴스
expression_index = ExpressionIndex()


@lru_cache(maxsize=1)
def get_expression_index() -> ExpressionIndex:
    """캐시된 인덱스 인스턴스 반환"""
    index = ExpressionIndex()
    if not index.is_loaded:
        index.load()
    return index
