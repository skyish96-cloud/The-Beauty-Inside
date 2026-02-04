"""
구조화 로깅 모듈
세션ID 포함 로깅
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Optional

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """JSON 형식의 구조화된 로그 포맷터"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 추가 컨텍스트 정보
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
            
        # 예외 정보
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class SessionLogger:
    """세션 ID가 포함된 로거 래퍼"""
    
    def __init__(self, logger: logging.Logger, session_id: Optional[str] = None):
        self._logger = logger
        self._session_id = session_id
    
    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        extra = {"session_id": self._session_id}
        if "latency_ms" in kwargs:
            extra["latency_ms"] = kwargs.pop("latency_ms")
        if "data" in kwargs:
            extra["extra_data"] = kwargs.pop("data")
        self._logger.log(level, msg, extra=extra, **kwargs)
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)
    
    def exception(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, exc_info=True, **kwargs)
    
    def with_session(self, session_id: str) -> "SessionLogger":
        """새 세션 ID로 로거 생성"""
        return SessionLogger(self._logger, session_id)


def setup_logging() -> None:
    """로깅 설정 초기화"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if settings.log_format == "json":
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def get_logger(name: str, session_id: Optional[str] = None) -> SessionLogger:
    """이름과 세션 ID로 로거 생성"""
    logger = logging.getLogger(name)
    return SessionLogger(logger, session_id)


# 기본 로거
logger = get_logger("beauty_inside")
