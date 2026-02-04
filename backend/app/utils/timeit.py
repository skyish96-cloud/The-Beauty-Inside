"""
Latency 측정 유틸리티
"""
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class Timer:
    """실행 시간 측정 클래스"""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_ms: float = 0.0
    
    def start(self) -> "Timer":
        """타이머 시작"""
        self.start_time = time.perf_counter()
        return self
    
    def stop(self) -> float:
        """타이머 중지, 경과 시간(ms) 반환"""
        if self.start_time is None:
            raise RuntimeError("Timer was not started")
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000
        return self.elapsed_ms
    
    def __enter__(self) -> "Timer":
        self.start()
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.stop()


@contextmanager
def measure_time(name: str = "operation", log: bool = True) -> Generator[Timer, None, None]:
    """
    컨텍스트 매니저로 실행 시간 측정
    
    사용 예:
        with measure_time("face_detection") as timer:
            detect_faces(image)
        print(f"Took {timer.elapsed_ms}ms")
    """
    timer = Timer(name)
    timer.start()
    try:
        yield timer
    finally:
        elapsed = timer.stop()
        if log:
            logger.debug(f"{name} completed", latency_ms=elapsed)


def timeit(name: Optional[str] = None, log: bool = True) -> Callable:
    """
    함수 실행 시간을 측정하는 데코레이터
    
    사용 예:
        @timeit("embedding_extraction")
        def extract_embedding(image):
            ...
    """
    def decorator(func: Callable) -> Callable:
        operation_name = name or func.__name__
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with measure_time(operation_name, log=log) as timer:
                result = func(*args, **kwargs)
            return result
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with measure_time(operation_name, log=log) as timer:
                result = await func(*args, **kwargs)
            return result
        
        # 비동기 함수인 경우 async wrapper 반환
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class StepTimer:
    """여러 단계의 실행 시간을 측정하는 클래스"""
    
    def __init__(self):
        self.steps: dict[str, float] = {}
        self.current_step: Optional[str] = None
        self.step_start: Optional[float] = None
        self.total_start: Optional[float] = None
    
    def start(self) -> "StepTimer":
        """전체 타이머 시작"""
        self.total_start = time.perf_counter()
        return self
    
    def step(self, name: str) -> "StepTimer":
        """새 단계 시작 (이전 단계 자동 종료)"""
        now = time.perf_counter()
        
        # 이전 단계 종료
        if self.current_step and self.step_start:
            self.steps[self.current_step] = (now - self.step_start) * 1000
        
        # 새 단계 시작
        self.current_step = name
        self.step_start = now
        return self
    
    def stop(self) -> dict:
        """타이머 종료, 모든 단계 시간 반환"""
        now = time.perf_counter()
        
        # 마지막 단계 종료
        if self.current_step and self.step_start:
            self.steps[self.current_step] = (now - self.step_start) * 1000
        
        # 총 시간
        if self.total_start:
            self.steps["total"] = (now - self.total_start) * 1000
        
        return self.steps
    
    @property
    def total_ms(self) -> float:
        """총 경과 시간 (ms)"""
        return self.steps.get("total", 0.0)
