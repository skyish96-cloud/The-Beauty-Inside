"""
ID 생성/검증 유틸리티
"""
from app.core.debug_tools import trace, trace_enabled, brief

import re
import secrets
import uuid
from datetime import datetime
from typing import Optional


# ID 접두사 정의
PREFIX_SESSION = "sess"
PREFIX_ANALYSIS = "anal"
PREFIX_RESULT = "rslt"
PREFIX_CELEB = "celb"


@trace("generate_session_id")
def generate_session_id() -> str:
    """
    세션 ID 생성
    형식: sess_{timestamp}_{random}
    예: sess_20240115_a1b2c3d4
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(4)
    return f"{PREFIX_SESSION}_{timestamp}_{random_part}"


@trace("generate_analysis_id")
def generate_analysis_id() -> str:
    """
    분석 ID 생성
    형식: anal_{uuid}
    """
    return f"{PREFIX_ANALYSIS}_{uuid.uuid4().hex[:12]}"


@trace("generate_result_id")
def generate_result_id() -> str:
    """
    결과 ID 생성
    형식: rslt_{uuid}
    """
    return f"{PREFIX_RESULT}_{uuid.uuid4().hex[:12]}"


@trace("generate_request_id")
def generate_request_id() -> str:
    """
    요청 추적용 ID 생성 (짧은 형식)
    """
    return secrets.token_hex(8)


# ID 패턴 정의
SESSION_ID_PATTERN = re.compile(r"^sess_\d{8}_[a-f0-9]{8}$")
ANALYSIS_ID_PATTERN = re.compile(r"^anal_[a-f0-9]{12}$")
RESULT_ID_PATTERN = re.compile(r"^rslt_[a-f0-9]{12}$")


@trace("validate_session_id")
def validate_session_id(session_id: str) -> bool:
    """세션 ID 유효성 검사"""
    if not session_id:
        return False
    return bool(SESSION_ID_PATTERN.match(session_id))


@trace("validate_analysis_id")
def validate_analysis_id(analysis_id: str) -> bool:
    """분석 ID 유효성 검사"""
    if not analysis_id:
        return False
    return bool(ANALYSIS_ID_PATTERN.match(analysis_id))


@trace("validate_result_id")
def validate_result_id(result_id: str) -> bool:
    """결과 ID 유효성 검사"""
    if not result_id:
        return False
    return bool(RESULT_ID_PATTERN.match(result_id))


@trace("extract_date_from_session_id")
def extract_date_from_session_id(session_id: str) -> Optional[datetime]:
    """세션 ID에서 날짜 추출"""
    if not validate_session_id(session_id):
        return None
    
    try:
        date_str = session_id.split("_")[1]
        return datetime.strptime(date_str, "%Y%m%d")
    except (IndexError, ValueError):
        return None


@trace("get_or_create_session_id")
def get_or_create_session_id(session_id: Optional[str]) -> str:
    """
    세션 ID가 없거나 유효하지 않으면 새로 생성
    """
    if session_id and validate_session_id(session_id):
        return session_id
    return generate_session_id()
