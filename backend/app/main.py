"""
Beauty Inside API 메인 모듈
FastAPI 생성/라우팅/WebSocket 등록
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.ws import router as ws_router
from app.core.config import settings
from app.core.errors import BeautyInsideError
from app.core.logger import get_logger, setup_logging
from app.core.model_loader import initialize_all_models
from app.infra.celeb_store.loader import get_celeb_loader
from app.infra.celeb_store.index import get_expression_index
from app.infra.firestore.client import init_firebase, is_firebase_enabled

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    # 시작 시
    logger.info("Starting Beauty Inside API...")
    
    # 로깅 설정
    setup_logging()
    
    # AI 모델 초기화 (자동 다운로드)
    model_status = initialize_all_models()
    if not model_status["mediapipe"] and not model_status["deepface"]:
        logger.warning("No AI models available - service may be limited")
    
    # Firebase 초기화 (설정된 경우)
    if is_firebase_enabled():
        try:
            init_firebase()
            logger.info("Firebase initialized")
        except Exception as e:
            logger.warning(f"Firebase initialization failed: {e}")
    
    # 연예인 데이터 사전 로딩
    try:
        loader = get_celeb_loader()
        if not loader.is_loaded:
            loader.load()
        logger.info(f"Loaded {len(loader.celebs)} celebrities")
        
        index = get_expression_index()
        if not index.is_loaded:
            index.load()
        logger.info(f"Expression index loaded: {index.expressions}")
        
    except Exception as e:
        logger.warning(f"Data loading failed: {e}")
    
    logger.info("Beauty Inside API started successfully")
    
    yield
    
    # 종료 시
    logger.info("Shutting down Beauty Inside API...")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="닮은 연예인 찾기 API - 얼굴 분석 및 유사도 매칭",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 예외 핸들러
@app.exception_handler(BeautyInsideError)
async def beauty_inside_exception_handler(request, exc: BeautyInsideError):
    """커스텀 예외 처리"""
    return JSONResponse(
        status_code=400,
        content={
            "error_code": exc.code.value,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """일반 예외 처리"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "E401",
            "message": "서버 내부 오류가 발생했습니다",
            "details": {"error": str(exc)} if settings.debug else {}
        }
    )


# 라우터 등록
app.include_router(ws_router, tags=["websocket"])


# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "debug": settings.debug
    }


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Beauty Inside API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None
    }


# 정적 파일 서빙 (연예인 이미지)
try:
    from pathlib import Path
    images_path = Path(settings.celeb_images_path)
    if images_path.exists():
        app.mount(
            "/celebs/images",
            StaticFiles(directory=str(images_path)),
            name="celeb_images"
        )
        logger.info(f"Serving static files from: {images_path}")
except Exception as e:
    logger.warning(f"Static file mount failed: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
