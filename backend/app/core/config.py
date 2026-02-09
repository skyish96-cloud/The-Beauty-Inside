"""
환경 설정 모듈
ENV 로드/검증 (파이어베이스/경로/옵션)
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 환경 설정"""
    
    model_config = ConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # 앱 기본 설정
    app_name: str = "Beauty Inside API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    api_base_url: str = "http://localhost:8000"  
    
    # WebSocket 설정
    ws_timeout_seconds: int = 30
    ws_max_message_size: int = 10 * 1024 * 1024  # 10MB
    
    # Firebase 설정
    firebase_credentials_path: Optional[str] = Field(default=None)
    firebase_project_id: Optional[str] = Field(default="the-beauty-inside")
    
    # 데이터 경로 설정
    data_dir: str = Field(default="data")
    celeb_embeddings_path: str = Field(default="data/celebs/embeddings")
    celeb_meta_path: str = Field(default="data/celebs/meta")
    celeb_images_path: str = Field(default="data/celebs/images")
    cache_dir: str = Field(default="data/cache")
    
    # 얼굴 분석 설정
    face_detection_confidence: float = 0.7
    face_embedding_model: str = "Facenet512"
    face_detector_backend: str = "retinaface"
    
    # 품질 검사 임계값
    min_face_size: int = 80  # 최소 얼굴 크기 (픽셀)
    max_faces: int = 1  # 최대 허용 얼굴 수
    blur_threshold: float = 100.0  # 흐림 임계값 (Laplacian variance)
    brightness_min: int = 40  # 최소 밝기
    brightness_max: int = 250  # 최대 밝기
    
    # 표정 분석 설정
    expression_confidence_threshold: float = 0.3
    supported_expressions: list[str] = ["neutral", "smile", "sad", "surprise"]
    
    # 랭킹 설정
    top_k: int = 3  # Top K 결과 수
    similarity_threshold: float = 0.4  # 최소 유사도 임계값

    # CORS 설정
    cors_origins: str = "http://localhost:8000,http://localhost:5173,http://localhost:5500,http://127.0.0.1:5173"
    cors_allow_credentials: bool = True
    cors_methods: str = "*"
    cors_allow_headers: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_origins or self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def cors_methods_list(self) -> list[str]:
        if not self.cors_methods or self.cors_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_methods.split(",")]
    
    # 로깅 설정
    log_level: str = "INFO"
    log_format: str = "json"
    
    @field_validator("data_dir", "celeb_embeddings_path", "celeb_meta_path", "celeb_images_path", "cache_dir")
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """경로 유효성 검사"""
        return v
    
    @property
    def celeb_embeddings_dir(self) -> Path:
        return Path(self.celeb_embeddings_path)
    
    @property
    def celeb_meta_dir(self) -> Path:
        return Path(self.celeb_meta_path)
    
    @property
    def celeb_images_dir(self) -> Path:
        return Path(self.celeb_images_path)
    
@lru_cache()
def get_settings() -> Settings:
    """캐시된 설정 인스턴스 반환"""
    return Settings()


# 전역 설정 접근용
settings = get_settings()
