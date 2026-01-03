"""유틸리티 함수"""
import os
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해시 생성"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def safe_float(value) -> float:
    """문자열을 안전하게 float로 변환 (콤마 제거)"""
    try:
        if value is None:
            return 0.0
        if isinstance(value, str):
            return float(value.replace(',', ''))
        return float(value)
    except (ValueError, AttributeError):
        return 0.0


def parse_date(date_str: Optional[str], format_str: str = "%Y-%m-%d") -> Optional[datetime.date]:
    """날짜 문자열을 date 객체로 변환"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, format_str).date()
    except (ValueError, TypeError):
        return None


def validate_file_upload(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
    """파일 업로드 검증"""
    if file_size > config.MAX_FILE_SIZE:
        return False, f"파일 크기가 {config.MAX_FILE_SIZE / (1024*1024):.0f}MB를 초과합니다."
    
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            return False, f"허용되지 않은 파일 형식입니다. 허용 형식: {', '.join(config.ALLOWED_EXTENSIONS)}"
    
    return True, None

