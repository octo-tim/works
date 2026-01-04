"""애플리케이션 설정 및 상수"""
import os

# 보안 설정
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn("SECRET_KEY 환경변수가 설정되지 않았습니다. 프로덕션 환경에서는 반드시 설정해야 합니다.")
    SECRET_KEY = "dev-secret-key-change-in-production"  # 개발용 기본값

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 400

# 관리자 설정 (환경변수로 관리)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "윤경식")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_DEPARTMENT = os.getenv("ADMIN_DEPARTMENT", "시스템사업부")

# 파일 업로드 설정
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.jpeg', '.png', '.gif'}

# 목표 연도
TARGET_YEAR = 2026

# 부서 매핑
DEPARTMENT_MAPPING = {
    'System': '시스템사업부',
    'Distribution': '유통사업부',
    'Management': '경영지원팀'
}


# AI 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
