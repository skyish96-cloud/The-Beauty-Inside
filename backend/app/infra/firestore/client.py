"""
Firebase Admin 초기화 모듈
"""
import os
from functools import lru_cache
from typing import Optional

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Firebase Admin SDK
_firebase_app = None
_firestore_client = None


def _get_credentials_path() -> Optional[str]:
    """serviceAccountKey.json 파일 경로 반환"""
    # 설정에 명시된 경로가 있으면 우선 사용
    if settings.firebase_credentials_path:
        return settings.firebase_credentials_path
    
    # 동적으로 serviceAccountKey.json 찾기
    # client.py 위치에서 3단계 위로(backend 폴더)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "..", "..", "..", "serviceAccountKey.json")
    
    if os.path.exists(json_path):
        logger.debug(f"Found serviceAccountKey.json at {json_path}")
        return json_path
    
    return None


def init_firebase() -> None:
    """Firebase 초기화"""
    global _firebase_app, _firestore_client
    
    if _firebase_app is not None:
        logger.debug("Firebase already initialized")
        return
    
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # 인증 정보 설정
        cred_path = _get_credentials_path()
        if cred_path:
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info(f"Firebase initialized with credentials file: {cred_path}")
        elif settings.firebase_project_id:
            # Application Default Credentials 사용
            _firebase_app = firebase_admin.initialize_app(
                options={"projectId": settings.firebase_project_id}
            )
            logger.info("Firebase initialized with project ID")
        else:
            logger.warning("Firebase credentials not configured, skipping initialization")
            return
        
        # Firestore 클라이언트 초기화
        _firestore_client = firestore.client()
        logger.info("Firestore client initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def get_firestore_client():
    """Firestore 클라이언트 반환"""
    global _firestore_client
    
    if _firestore_client is None:
        init_firebase()
    
    return _firestore_client


def is_firebase_enabled() -> bool:
    """Firebase가 활성화되어 있는지 확인"""
    return bool(settings.firebase_credentials_path or settings.firebase_project_id)


class FirestoreClientManager:
    """Firestore 클라이언트 관리자 (의존성 주입용)"""
    
    def __init__(self):
        self._client = None
        self._enabled = is_firebase_enabled()
    
    @property
    def client(self):
        if not self._enabled:
            return None
        if self._client is None:
            self._client = get_firestore_client()
        return self._client
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def collection(self, name: str):
        """컬렉션 참조 반환"""
        if not self._enabled or self.client is None:
            return None
        return self.client.collection(name)


# 전역 매니저 인스턴스
firestore_manager = FirestoreClientManager()
