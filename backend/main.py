"""
Beauty Inside API 메인 모듈
FastAPI 생성/라우팅/WebSocket 등록
"""
from app.core.debug_tools import trace, trace_enabled, brief

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
from app.core.diagnostics import log_startup_diagnostics
from app.infra.celeb_store.loader import get_celeb_loader
from app.infra.celeb_store.index import get_expression_index

logger = get_logger(__name__)



if trace_enabled():
    logger.info("[TRACE] module loaded", data={"module": __name__})

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""    # 시작 시
    # 로깅 설정 (가장 먼저)
    setup_logging()

    logger.info("Starting Beauty Inside API...")
    # 진단 로그 (debug/trace 모드에서만)
    log_startup_diagnostics()

    # AI 모델 초기화 (자동 다운로드)
    model_status = initialize_all_models()
    if not model_status["mediapipe"] and not model_status["deepface"]:
        logger.warning("No AI models available - service may be limited")
    
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
    # docs_url="/docs" if settings.debug else None,
    # redoc_url="/redoc" if settings.debug else None,
)


# CORS 설정 (환경 변수로 관리)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods_list,
    allow_headers=[settings.cors_allow_headers] if settings.cors_allow_headers == "*" else settings.cors_allow_headers.split(","),
)


# Request timing middleware (HTTP용)
@app.middleware("http")
async def _timing_middleware(request, call_next):
    if not trace_enabled():
        return await call_next(request)
    import time
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        dt = (time.perf_counter() - t0) * 1000
        try:
            logger.info("HTTP request", data={"method": request.method, "path": str(request.url.path), "latency_ms": dt})
        except Exception:
            pass


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


# 정적 파일 서빙 - 연예인 이미지
from pathlib import Path
from fastapi.responses import FileResponse
celeb_images_path = Path(__file__).parent.parent / "data" / "celebs" / "images" / "famous"

# 이미지 제공 API (CORS 포함)
@app.get("/api/celeb-image/{filename}")
async def get_celeb_image(filename: str):
    """연예인 이미지 제공 (CORS 헤더 포함)"""
    file_path = celeb_images_path / filename
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    # CORS 헤더는 미들웨어에서 처리됨
    return FileResponse(file_path)


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
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
