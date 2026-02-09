"""
디버깅/트레이싱 유틸리티
- 환경변수 BI_TRACE=1 또는 settings.debug=True 일 때, 함수 입/출력/예외를 구조화 로그로 남김
- 과도한 로그를 피하기 위해 값 요약(brief)만 기록
"""
from __future__ import annotations

import inspect
import os
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from app.core.config import settings
from app.core.logger import get_logger

_logger = get_logger(__name__)

_TRUTHY = {"1", "true", "yes", "y", "on"}
_FALSY = {"0", "false", "no", "n", "off"}

def trace_enabled() -> bool:
    """
    트레이스(디버그) 로깅 활성화 여부.
    우선순위:
      1) BI_TRACE 환경변수
      2) settings.debug
    """
    v = os.getenv("BI_TRACE")
    if v is not None:
        return v.strip().lower() in _TRUTHY
    return bool(getattr(settings, "debug", False))

def _truncate(s: str, n: int = 160) -> str:
    if s is None:
        return ""
    return s if len(s) <= n else s[:n] + f"...(len={len(s)})"

def brief(value: Any) -> Any:
    """
    로그에 넣기 위한 안전 요약.
    - numpy 배열: shape/dtype/min/max/NaN 여부
    - bytes: 길이
    - str(base64 포함): 길이 + prefix 일부
    - dict/list: 길이만
    """
    try:
        import numpy as np  # optional
    except Exception:
        np = None  # type: ignore

    try:
        if value is None:
            return None

        # numpy
        if np is not None and isinstance(value, getattr(np, "ndarray", ())):
            arr = value
            info: Dict[str, Any] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
            try:
                info["min"] = float(arr.min())
                info["max"] = float(arr.max())
            except Exception:
                pass
            try:
                info["has_nan"] = bool(getattr(np, "isnan")(arr).any())
            except Exception:
                pass
            return info

        if isinstance(value, (bytes, bytearray)):
            return {"bytes_len": len(value)}

        if isinstance(value, str):
            # base64/데이터URL는 너무 길어서 길이+앞부분만
            return {"str_len": len(value), "prefix": _truncate(value, 80)}

        if isinstance(value, dict):
            return {"dict_keys": list(value.keys())[:30], "dict_len": len(value)}

        if isinstance(value, (list, tuple, set)):
            return {"len": len(value)}

        # pydantic model
        if hasattr(value, "model_dump"):
            return {"pydantic": value.__class__.__name__}

        return _truncate(str(value), 160)
    except Exception as e:
        return f"<brief_error {e!r}>"

def _args_summary(func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Dict[str, Any]:
    try:
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        # 너무 길어지지 않게 상위 몇 개만
        out: Dict[str, Any] = {}
        for k, v in list(bound.arguments.items())[:12]:
            out[k] = brief(v)
        return out
    except Exception:
        return {"args_len": len(args), "kwargs_keys": list(kwargs.keys())[:12]}

def trace(name: Optional[str] = None) -> Callable:
    """
    함수 트레이스 데코레이터 (sync/async 지원).
    - entry/exit + 실행시간
    - 예외 발생 시 stacktrace 포함
    """
    def decorator(func: Callable) -> Callable:
        op = name or getattr(func, "__qualname__", getattr(func, "__name__", "op"))

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def aw(*args: Any, **kwargs: Any) -> Any:
                if not trace_enabled():
                    return await func(*args, **kwargs)

                t0 = time.perf_counter()
                _logger.info(f"[TRACE] enter {op}", data={"args": _args_summary(func, args, kwargs)})
                try:
                    res = await func(*args, **kwargs)
                    dt = (time.perf_counter() - t0) * 1000
                    _logger.info(f"[TRACE] exit  {op}", latency_ms=dt, data={"result": brief(res)})
                    return res
                except Exception as e:
                    dt = (time.perf_counter() - t0) * 1000
                    _logger.exception(f"[TRACE] error {op}: {e}", latency_ms=dt, data={"args": _args_summary(func, args, kwargs)})
                    raise

            return aw

        @wraps(func)
        def sw(*args: Any, **kwargs: Any) -> Any:
            if not trace_enabled():
                return func(*args, **kwargs)

            t0 = time.perf_counter()
            _logger.info(f"[TRACE] enter {op}", data={"args": _args_summary(func, args, kwargs)})
            try:
                res = func(*args, **kwargs)
                dt = (time.perf_counter() - t0) * 1000
                _logger.info(f"[TRACE] exit  {op}", latency_ms=dt, data={"result": brief(res)})
                return res
            except Exception as e:
                dt = (time.perf_counter() - t0) * 1000
                _logger.exception(f"[TRACE] error {op}: {e}", latency_ms=dt, data={"args": _args_summary(func, args, kwargs)})
                raise

        return sw

    return decorator
