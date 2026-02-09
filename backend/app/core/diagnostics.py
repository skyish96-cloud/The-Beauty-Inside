"""
런타임 진단(디버깅) 모듈
- 모델/데이터 파일 존재 여부, 버전, 주요 설정을 한 번에 로그로 남김
"""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings
from app.core.logger import get_logger
from app.core.debug_tools import brief, trace_enabled

logger = get_logger(__name__)

def _pkg_version(name: str) -> str:
    try:
        import importlib.metadata as md
        return md.version(name)
    except Exception:
        return "not-installed"

def collect_diagnostics() -> Dict[str, Any]:
    models_dir = (Path(__file__).parent.parent.parent / "models").resolve()
    data_dir = Path(settings.data_dir).resolve()

    info: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pid": os.getpid(),
        "debug": settings.debug,
        "log_level": settings.log_level,
        "ws_timeout_seconds": settings.ws_timeout_seconds,
        "data_dir": str(data_dir),
        "models_dir": str(models_dir),
        "packages": {
            "fastapi": _pkg_version("fastapi"),
            "uvicorn": _pkg_version("uvicorn"),
            "numpy": _pkg_version("numpy"),
            "opencv-python": _pkg_version("opencv-python"),
            "mediapipe": _pkg_version("mediapipe"),
            "deepface": _pkg_version("deepface"),
            "tensorflow": _pkg_version("tensorflow"),
            "torch": _pkg_version("torch"),
        },
        "paths": {
            "embeddings_npy": str(Path(settings.celeb_embeddings_path).resolve() / "embed.npy"),
            "ids_npy": str(Path(settings.celeb_embeddings_path).resolve() / "ids.npy"),
            "expr_index_json": str(Path(settings.celeb_embeddings_path).resolve() / "expr_index.json"),
            "celebs_csv": str(Path(settings.celeb_meta_path).resolve() / "celebs.csv"),
            "images_dir": str(Path(settings.celeb_images_path).resolve()),
        },
    }

    # 존재/크기
    file_stats: Dict[str, Any] = {}
    for k, p in info["paths"].items():
        try:
            path = Path(p)
            file_stats[k] = {
                "exists": path.exists(),
                "is_dir": path.is_dir(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            }
        except Exception as e:
            file_stats[k] = {"error": str(e)}
    info["file_stats"] = file_stats
    return info

def log_startup_diagnostics() -> None:
    if not trace_enabled() and not settings.debug:
        return
    info = collect_diagnostics()
    logger.info("Startup diagnostics", data={"diag": info})
