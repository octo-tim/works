import os
from dotenv import load_dotenv

# .env 파일을 절대 경로로 지정하여 로드
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# AI 설정
# 환경 변수 로드 실패 시 하드코딩된 키 사용 (사용자 제공)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAmhhh66lRiGHtzsfUYMQxCMXORhr7pr8M")

if not GEMINI_API_KEY:
    print("[ERROR] GEMINI_API_KEY is missing!")
else:
    print(f"[DEBUG] GEMINI_API_KEY loaded: {GEMINI_API_KEY[:5]}...")


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


