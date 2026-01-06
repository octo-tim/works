from fastapi import FastAPI, Depends, Request, Form, status, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import traceback
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from typing import Optional, List
from datetime import date, datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import config
import utils
import google.generativeai as genai
import json
import re
import wbs_templates # Template Module
import fix_production_schema # Import migration script

# ---------------------------------------------------------
# AUTO-MIGRATION FOR PRODUCTION (Added by AI)
# This ensures missing columns are added on server startup
try:
    print("Running schema migration check...")
    # Pass database URL from config or env if needed, but the script handles env var
    # We call it directly. Note: It needs DATABASE_URL env var which Render provides.
    fix_production_schema.fix_schema()
except Exception as e:
    print(f"Migration warning: {e}")
# ---------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependency
def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    """현재 로그인한 사용자 가져오기"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    return user


def require_auth(current_user: Optional[models.User] = Depends(get_current_user)):
    """인증이 필요한 라우트를 위한 의존성"""
    if not current_user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    return current_user


def require_admin(current_user: models.User = Depends(require_auth)):
    """관리자 권한이 필요한 라우트를 위한 의존성"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return current_user


# 데이터베이스 초기화
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Startup DB Error: {e}")

app = FastAPI(title="비즈니스 일정 공유 시스템", version="1.0.0")

# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = "".join(traceback.format_exception(None, exc, exc.__traceback__))
    print(f"Global Error: {error_msg}")
    # 프로덕션에서는 상세 에러를 숨기는 것이 좋습니다
    # if os.getenv("DEBUG", "False").lower() == "true":
    if True:
        return HTMLResponse(
            status_code=500,
            content=f"<h1>Internal Server Error</h1><pre>{error_msg}</pre>"
        )
    return HTMLResponse(
        status_code=500,
        content="<h1>Internal Server Error</h1><p>서버 오류가 발생했습니다. 관리자에게 문의하세요.</p>"
    )

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

def populate_db(db: Session):
    """초기 데이터베이스 데이터 생성"""
    # 관리자 사용자 생성/업데이트
    if not config.ADMIN_PASSWORD:
        print("경고: ADMIN_PASSWORD 환경변수가 설정되지 않았습니다. 관리자 계정이 생성되지 않습니다.")
        return
    
    admin_user = db.query(models.User).filter(models.User.username == config.ADMIN_USERNAME).first()
    if not admin_user:
        admin_user = models.User(
            username=config.ADMIN_USERNAME,
            password_hash=utils.get_password_hash(config.ADMIN_PASSWORD),
            department=config.ADMIN_DEPARTMENT,
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        print(f"관리자 사용자 생성: {config.ADMIN_USERNAME}")
    elif config.ADMIN_PASSWORD:
        # 비밀번호가 환경변수로 제공된 경우에만 업데이트
        admin_user.password_hash = utils.get_password_hash(config.ADMIN_PASSWORD)
        db.commit()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[{datetime.now()}] GLOBAL LOG: {request.method} {request.url}")
    response = await call_next(request)
    print(f"[{datetime.now()}] GLOBAL LOG: Response {response.status_code}")
    return response

@app.on_event("startup")
def on_startup():
    print(f"[{datetime.now()}] APP VERSION 1.7 LOADED")
    db = SessionLocal()
    populate_db(db)
    db.close()
    print("서버 시작 중...")
    try:
        db = SessionLocal()
        try:
            from sqlalchemy import text
            
            # 마이그레이션: creator_id 컬럼 추가
            try:
                db.execute(text("SELECT creator_id FROM projects LIMIT 1"))
            except Exception:
                db.rollback()
                print("마이그레이션: projects 테이블에 creator_id 컬럼 추가")
                db.execute(text("ALTER TABLE projects ADD COLUMN creator_id INTEGER REFERENCES users(id)"))
                db.commit()
            
            try:
                db.execute(text("SELECT creator_id FROM tasks LIMIT 1"))
            except Exception:
                db.rollback()
                print("마이그레이션: tasks 테이블에 creator_id 컬럼 추가")
                db.execute(text("ALTER TABLE tasks ADD COLUMN creator_id INTEGER REFERENCES users(id)"))
                db.commit()
            
            # 마이그레이션: 사용자 테이블에 추가 컬럼 추가
            columns_to_add = ["email", "phone", "position"]
            for col in columns_to_add:
                try:
                    db.execute(text(f"ALTER TABLE users ADD COLUMN {col} VARCHAR"))
                    db.commit()
                    print(f"마이그레이션: users 테이블에 {col} 컬럼 추가")
                except Exception:
                    db.rollback()
                    # 컬럼이 이미 존재하는 경우 무시
            
            # 마이그레이션: 부서명 한글화
            for eng, kor in config.DEPARTMENT_MAPPING.items():
                db.execute(text(f"UPDATE users SET department = '{kor}' WHERE department = '{eng}'"))
                db.execute(text(f"UPDATE projects SET department = '{kor}' WHERE department = '{eng}'"))
                db.execute(text(f"UPDATE tasks SET department = '{kor}' WHERE department = '{eng}'"))
            db.commit()
            
            populate_db(db)
        finally:
            db.close()
        print("서버 시작 완료")
    except Exception as e:
        print(f"시작 오류: {e}")

# 개발용 디버그 라우트 (프로덕션에서는 제거 권장)
@app.get("/reset_admin", response_class=HTMLResponse)
def reset_admin(db: Session = Depends(get_db)):
    """관리자 계정 리셋 (개발용)"""
    if not config.ADMIN_PASSWORD:
        return HTMLResponse(
            status_code=400,
            content="<h1>오류</h1><p>ADMIN_PASSWORD 환경변수가 설정되지 않았습니다.</p>"
        )
    
    user = db.query(models.User).filter(models.User.username == config.ADMIN_USERNAME).first()
    if not user:
        user = models.User(
            username=config.ADMIN_USERNAME,
            password_hash=utils.get_password_hash(config.ADMIN_PASSWORD),
            department=config.ADMIN_DEPARTMENT,
            role="admin"
        )
        db.add(user)
        msg = "관리자 사용자가 생성되었습니다."
    else:
        user.password_hash = utils.get_password_hash(config.ADMIN_PASSWORD)
        msg = f"관리자 비밀번호가 업데이트되었습니다."
    
    db.commit()
    return HTMLResponse(content=f"<h1>완료</h1><p>{msg}</p><a href='/login'>로그인 페이지로 이동</a>")

@app.get("/health/db", response_class=HTMLResponse)
def health_check_db(db: Session = Depends(get_db)):
    try:
        user_count = db.query(models.User).count()
        return f"<h1>✅ Database is Healthy</h1><p>Connection successful.</p><p>Total Users: {user_count}</p><p>DB URL: {engine.url}</p>"
    except Exception as e:
        import traceback
        error_msg = "".join(traceback.format_exception(None, e, e.__traceback__))
        print(f"DB Health Error: {error_msg}")
        return f"<h1>❌ Database Error</h1><pre>{error_msg}</pre>"



# --- Page Routes ---


# --- Auth Routes ---
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """사용자 로그인"""
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not utils.verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "사용자명 또는 비밀번호가 올바르지 않습니다."})
    
    access_token = utils.create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite="lax")
    return response

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(request: Request, username: str = Form(...), password: str = Form(...), department: str = Form(...), db: Session = Depends(get_db)):
    """사용자 회원가입"""
    try:
        if db.query(models.User).filter(models.User.username == username).first():
            return templates.TemplateResponse("signup.html", {"request": request, "error": "이미 존재하는 사용자명입니다."})
        
        new_user = models.User(
            username=username,
            password_hash=utils.get_password_hash(password),
            department=department,
            role="admin" if username == config.ADMIN_USERNAME else "user"
        )
        db.add(new_user)
        db.commit()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        print(f"회원가입 오류: {e}")
        return templates.TemplateResponse("signup.html", {"request": request, "error": f"회원가입 실패: {str(e)}"})

@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, 
              assignee_id: Optional[str] = None, 
              department: Optional[str] = None, 
              project_id: Optional[str] = None,
              target_month: Optional[int] = None,
              db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    
    if not current_user:
        return RedirectResponse(url="/login")
    
    # 기본값: 현재 월
    if target_month is None:
        target_month = datetime.now().month
    
    query = db.query(models.Task)
    
    # 부서별 필터링 로직 (일반 사용자만 강제 적용, 관리자는 전체)
    if current_user.role != "admin":
        # 일반 사용자는 자신의 부서 데이터만 조회
        department = current_user.department
        query = query.filter(models.Task.department == department)
    
    tasks = query.all()

    today = datetime.now().date()

    # Organized for Dashboard
    tasks_todo = [t for t in tasks if t.status == 'Todo']
    
    # In Progress: Status is 'In Progress' OR (Date matches Today AND Status != 'Done')
    tasks_inprogress = []
    for t in tasks:
        is_active_today = False
        if t.start_date and t.due_date:
            if t.start_date <= today <= t.due_date:
                is_active_today = True
        elif t.start_date: # Start date only
             if t.start_date <= today:
                 is_active_today = True
        elif t.due_date: # Due date only
             if t.due_date >= today: # Looser condition? Or strict? Let's say if due date is today or future. Actually usually if due date only, it's active until then.
                 # Let's keep it simple: matches existing In Progress logic or explicitly overlaps today.
                 if t.due_date == today:
                     is_active_today = True

        if t.status == 'In Progress' or (is_active_today and t.status != 'Done'):
             tasks_inprogress.append(t)

    tasks_done = [t for t in tasks if t.status == 'Done']

    # Serialize for Calendar
    calendar_events = []
    for t in tasks:
        # Determine color
        color = "#6B7280" # Gray (Todo)
        if t.status == "In Progress":
            color = "#3B82F6" # Blue
        elif t.status == "Done":
            color = "#10B981" # Green
        
        # Determine dates
        start = t.start_date
        end = t.due_date
        
        if not start and not end:
            continue # Skip tasks with no dates
        
        event = {
            "title": f"[{t.assignee.username if t.assignee else '미지정'}] {t.title}",
            "url": f"javascript:openEditModal('{t.id}', '{t.title}', '{t.description or ''}', '{t.status}', '{t.department or ''}', {[u.id for u in t.assignees]}, '{t.start_date or ''}', '{t.due_date or ''}', '{t.project_id or 0}', {[f.filename for f in t.files]}, {[f.filepath for f in t.files]})"
        }

        if start:
            event["start"] = start.strftime('%Y-%m-%d')
        else:
            event["start"] = end.strftime('%Y-%m-%d') # Fallback to due date if no start
            
        if end and start and end >= start:
            # FullCalendar end is exclusive, so add 1 day
            # But we must be careful not to modify the DB object, use local var
            # Convert to datetime to add day? model uses date.
            # actually we can just use string manipulation or datetime logic
            next_day = end + timedelta(days=1)
            event["end"] = next_day.strftime('%Y-%m-%d')
        elif end and not start:
             # Only due date. Make it all day.
            pass 

        calendar_events.append(event)



    # Fetch Today's Checks
    # today predefined above
    todays_checks = db.query(models.TodaysCheck).filter(
        models.TodaysCheck.date == today,
        (models.TodaysCheck.sender_id == current_user.id) | (models.TodaysCheck.receiver_id == current_user.id)
    ).all()

    # Fetch Today's Events (Schedule)
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    event_query = db.query(models.Event).filter(
        models.Event.start_time >= today_start,
        models.Event.start_time <= today_end
    )
    
    if current_user.role != "admin":
        event_query = event_query.filter(models.Event.department == current_user.department)
        
    db_events = event_query.all()
    
    todays_events = []
    for e in db_events:
        todays_events.append({
            "title": e.title,
            "description": e.description,
            "start_time": e.start_time.strftime("%H:%M"),
            "end_time": e.end_time.strftime("%H:%M") if e.end_time else "",
            "is_all_day": e.is_all_day,
            "user_name": e.user.username if e.user else "Unknown"
        })

    users = db.query(models.User).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": current_user,
        "tasks_todo": tasks_todo,
        "tasks_inprogress": tasks_inprogress,
        "tasks_done": tasks_done,
        "todays_checks": todays_checks, 
        "todays_events": todays_events, # Pass to template
        "calendar_events": calendar_events, # Pass to template

        "users": users,
        "users": users,
        "projects": db.query(models.Project).all(), # Pass projects for modal
        "selected_month": target_month,
        "goals": {
            "annual_2026": db.query(models.AnnualGoal).filter(models.AnnualGoal.year == config.TARGET_YEAR).first(),
            "monthly_obj_system": db.query(models.MonthlyObjective).filter(
                models.MonthlyObjective.year == config.TARGET_YEAR,
                models.MonthlyObjective.month == target_month,
                models.MonthlyObjective.division == 'System'
            ).first(),
            "monthly_obj_dist": db.query(models.MonthlyObjective).filter(
                models.MonthlyObjective.year == config.TARGET_YEAR,
                models.MonthlyObjective.month == target_month,
                models.MonthlyObjective.division == 'Distribution'
            ).first(),
            "monthly_perf_system": db.query(models.MonthlyPerformance).filter(
                models.MonthlyPerformance.year == config.TARGET_YEAR,
                models.MonthlyPerformance.month == target_month,
                models.MonthlyPerformance.division == 'System'
            ).first(),
            "monthly_perf_dist": db.query(models.MonthlyPerformance).filter(
                models.MonthlyPerformance.year == config.TARGET_YEAR,
                models.MonthlyPerformance.month == target_month,
                models.MonthlyPerformance.division == 'Distribution'
            ).first()
        }
    })

@app.post("/goals/annual", response_class=RedirectResponse)
def update_annual_goal(request: Request, year: int = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    goal = db.query(models.AnnualGoal).filter(models.AnnualGoal.year == year).first()
    if not goal:
        goal = models.AnnualGoal(year=year, content=content)
        db.add(goal)
    else:
        goal.content = content
    db.commit()
    return RedirectResponse(url=request.headers.get("referer"), status_code=303)

@app.post("/goals/objective", response_class=RedirectResponse)
def update_monthly_objective(request: Request, year: int = Form(...), month: int = Form(...), division: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    obj = db.query(models.MonthlyObjective).filter(models.MonthlyObjective.year == year, models.MonthlyObjective.month == month, models.MonthlyObjective.division == division).first()
    if not obj:
        obj = models.MonthlyObjective(year=year, month=month, division=division, content=content)
        db.add(obj)
    else:
        obj.content = content
    db.commit()
    return RedirectResponse(url=request.headers.get("referer"), status_code=303)

@app.post("/goals/performance", response_class=RedirectResponse)
def update_monthly_performance(request: Request, year: int = Form(...), month: int = Form(...), division: str = Form(...), field: str = Form(...), value: str = Form(...), db: Session = Depends(get_db)):
    # field is either "goal_value" or "actual_value"
    perf = db.query(models.MonthlyPerformance).filter(models.MonthlyPerformance.year == year, models.MonthlyPerformance.month == month, models.MonthlyPerformance.division == division).first()
    if not perf:
        perf = models.MonthlyPerformance(year=year, month=month, division=division)
        db.add(perf)
    
    if field == "goal_value":
        perf.goal_value = value
    elif field == "actual_value":
        perf.actual_value = value
        
    db.commit()
    return RedirectResponse(url=request.headers.get("referer"), status_code=303)


@app.get("/octovision", response_class=HTMLResponse)
def read_octovision(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """목표관리 페이지"""
    if not current_user:
        return RedirectResponse(url="/login")
    
    perf_sys = db.query(models.MonthlyPerformance).filter(
        models.MonthlyPerformance.year == config.TARGET_YEAR,
        models.MonthlyPerformance.division == 'System'
    ).all()
    perf_dist = db.query(models.MonthlyPerformance).filter(
        models.MonthlyPerformance.year == config.TARGET_YEAR,
        models.MonthlyPerformance.division == 'Distribution'
    ).all()
    
    # 총계 계산
    total_goal_sys = sum(utils.safe_float(p.goal_value) for p in perf_sys)
    total_actual_sys = sum(utils.safe_float(p.actual_value) for p in perf_sys)
    total_goal_dist = sum(utils.safe_float(p.goal_value) for p in perf_dist)
    total_actual_dist = sum(utils.safe_float(p.actual_value) for p in perf_dist)

    return templates.TemplateResponse("octovision.html", {
        "request": request,
        "user": current_user,
        "goals": {
            "annual_2026": db.query(models.AnnualGoal).filter(models.AnnualGoal.year == config.TARGET_YEAR).first(),
            "objectives_system": {
                g.month: g.content for g in db.query(models.MonthlyObjective).filter(
                    models.MonthlyObjective.year == config.TARGET_YEAR,
                    models.MonthlyObjective.division == 'System'
                ).all()
            },
            "objectives_dist": {
                g.month: g.content for g in db.query(models.MonthlyObjective).filter(
                    models.MonthlyObjective.year == config.TARGET_YEAR,
                    models.MonthlyObjective.division == 'Distribution'
                ).all()
            },
            "performance_system": {g.month: g for g in perf_sys},
            "performance_dist": {g.month: g for g in perf_dist},
            "totals": {
                "sys_goal": f"{int(total_goal_sys):,}",
                "sys_actual": f"{int(total_actual_sys):,}",
                "dist_goal": f"{int(total_goal_dist):,}",
                "dist_actual": f"{int(total_actual_dist):,}"
            },
            "schedules_system": group_schedules_by_month(
                db.query(models.KeySchedule).filter(models.KeySchedule.division == 'System').all()
            ),
            "schedules_dist": group_schedules_by_month(
                db.query(models.KeySchedule).filter(models.KeySchedule.division == 'Distribution').all()
            )
        }
    })

def group_schedules_by_month(schedules):
    """일정을 월별로 그룹화"""
    grouped = {}
    for s in schedules:
        if s.date.year == config.TARGET_YEAR:
            if s.date.month not in grouped:
                grouped[s.date.month] = []
            grouped[s.date.month].append(s)
    # 날짜순 정렬
    for m in grouped:
        grouped[m].sort(key=lambda x: x.date)
    return grouped

@app.post("/goals/schedule", response_class=RedirectResponse)
def update_key_schedule(request: Request, date_str: str = Form(...), division: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    """주요 일정 추가"""
    sched_date = utils.parse_date(date_str, "%Y-%m-%d")
    if not sched_date:
        return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)
    
    schedule = models.KeySchedule(date=sched_date, division=division, content=content)
    db.add(schedule)
    db.commit()
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)

@app.post("/tasks/create", response_class=RedirectResponse)
def create_task(title: str = Form(...), 
                description: str = Form(None),
                status: str = Form("Todo"),
                start_date: str = Form(None),
                due_date: str = Form(None),
                project_id: int = Form(None),
                assignee_ids: List[int] = Form([]),
                department: str = Form(None),
                db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    """업무 생성"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    start_date_obj = utils.parse_date(start_date, "%Y-%m-%d")
    due_date_obj = utils.parse_date(due_date, "%Y-%m-%d")
    
    # 0을 None으로 변환
    # 0을 None으로 변환
    project_id = None if project_id == 0 else project_id

    new_task = models.Task(
        title=title,
        description=description,
        status=status,
        start_date=start_date_obj,
        due_date=due_date_obj,
        project_id=project_id,
        department=department,
        creator_id=current_user.id
    )
    db.add(new_task)
    db.commit()
    
    # 다중 담당자 처리
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        new_task.assignees = users
        # 레거시 지원
        if users:
            new_task.assignee_id = users[0].id
        db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/tasks/update_status/{task_id}")
def update_task_status(task_id: int, status: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """업무 상태 업데이트"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.status = status
        db.commit()
    return RedirectResponse(url="/", status_code=303)

    return RedirectResponse(url="/", status_code=303)


@app.post("/todays_check/create", response_class=RedirectResponse)
def create_todays_check(receiver_id: int = Form(...), content: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """오늘의 확인 메시지 생성"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    new_check = models.TodaysCheck(
        content=content,
        sender_id=current_user.id,
        receiver_id=receiver_id
    )
    db.add(new_check)
    db.commit()
    return RedirectResponse(url="/", status_code=303)
@app.get("/admin", response_class=HTMLResponse)
def read_admin(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """관리자 페이지"""
    users = db.query(models.User).all()
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "user": current_user,
        "users": users
    })

@app.post("/admin/users", response_class=RedirectResponse)
def create_user(username: str = Form(...), 
                department: str = Form(None),
                email: str = Form(None),
                phone: str = Form(None),
                position: str = Form(None),
                password: str = Form(...),
                db: Session = Depends(get_db),
                current_user: models.User = Depends(require_admin)):
    """사용자 생성"""
    # 중복 사용자명 체크
    if db.query(models.User).filter(models.User.username == username).first():
        return RedirectResponse(url="/admin?error=duplicate_username", status_code=303)
    
    new_user = models.User(
        username=username,
        department=department,
        email=email,
        phone=phone,
        position=position,
        password_hash=utils.get_password_hash(password)
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/users/{user_id}/update", response_class=RedirectResponse)
def update_user(user_id: int, 
                username: str = Form(...),
                department: str = Form(None),
                email: str = Form(None),
                phone: str = Form(None),
                position: str = Form(None),
                password: str = Form(None),
                db: Session = Depends(get_db),
                current_user: models.User = Depends(require_admin)):
    """사용자 정보 업데이트"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/admin", status_code=303)
    
    # 사용자명 중복 체크 (자신 제외)
    existing_user = db.query(models.User).filter(
        models.User.username == username,
        models.User.id != user_id
    ).first()
    if existing_user:
        return RedirectResponse(url="/admin?error=duplicate_username", status_code=303)
    
    user.username = username
    user.department = department
    user.email = email
    user.phone = phone
    user.position = position
    
    if password and password.strip():
        user.password_hash = utils.get_password_hash(password)
    
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/users/{user_id}/delete", response_class=RedirectResponse)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """사용자 삭제"""
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        return RedirectResponse(url="/admin", status_code=303)
    
    # 자신을 삭제하는 것 방지
    if user_to_delete.id == current_user.id:
        return RedirectResponse(url="/admin?error=cannot_delete_self", status_code=303)

    # 1. 생성한 프로젝트/업무에서 creator_id 제거
    db.query(models.Project).filter(models.Project.creator_id == user_id).update({"creator_id": None})
    db.query(models.Task).filter(models.Task.creator_id == user_id).update({"creator_id": None})
    
    # 2. 할당된 업무에서 assignee_id 제거 (레거시)
    db.query(models.Task).filter(models.Task.assignee_id == user_id).update({"assignee_id": None})
    
    # 3. 다대다 관계에서 제거
    db.execute(models.project_assignees.delete().where(models.project_assignees.c.user_id == user_id))
    db.execute(models.task_assignees.delete().where(models.task_assignees.c.user_id == user_id))
    
    # 4. 사용자 삭제
    db.delete(user_to_delete)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)



@app.get("/projects", response_class=HTMLResponse)
def read_projects(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """프로젝트 목록 페이지"""
    if not current_user:
        return RedirectResponse(url="/login")
    
    try:
        projects = db.query(models.Project).all()
        scheduled = [p for p in projects if p.status == 'Scheduled']
        inprogress = [p for p in projects if p.status == 'In Progress']
        completed = [p for p in projects if p.status == 'Completed']
        
        users = db.query(models.User).all()

        return templates.TemplateResponse("projects.html", {
            "request": request,
            "user": current_user,
            "scheduled": scheduled, 
            "inprogress": inprogress, 
            "completed": completed,
            "users": users
        })
    except Exception as e:
        print(f"Project Page Error: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"<h1>Internal Server Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", status_code=500)

@app.post("/projects", response_class=RedirectResponse)
def create_project(name: str = Form(...), description: str = Form(None), 
                   start_date: str = Form(None), end_date: str = Form(None), 
                   status: str = Form(...),
                   department: str = Form(None),
                   assignee_ids: List[int] = Form([]),
                   suggested_tasks: str = Form(None), # JSON string of tasks
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    """프로젝트 생성"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Check for duplicate project name
    existing_project = db.query(models.Project).filter(models.Project.name == name).first()
    if existing_project:
        return RedirectResponse(url="/projects?error=duplicate_name", status_code=303)
    
    # YYYY-MM 형식 처리
    s_date = utils.parse_date(start_date, "%Y-%m") if start_date else None
    e_date = utils.parse_date(end_date, "%Y-%m") if end_date else None
    
    new_project = models.Project(
        name=name, 
        description=description, 
        start_date=s_date, 
        end_date=e_date, 
        status=status, 
        department=department,
        creator_id=current_user.id
    )
    db.add(new_project)
    db.commit()
    
    # 담당자 처리
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        new_project.assignees = users
        db.commit()

    # AI 제안 업무 생성
    if suggested_tasks:
        try:
            tasks_list = json.loads(suggested_tasks)
            for t_data in tasks_list:
                if not t_data.get('title'): continue
                
                # 날짜 계산: 프로젝트 시작일 기준 (없으면 오늘)
                p_start = s_date if s_date else date.today()
                est_days = int(t_data.get('estimated_days', 1))
                t_due = p_start + timedelta(days=est_days)
                
                new_task = models.Task(
                    title=t_data['title'],
                    description=t_data.get('description'),
                    status="Todo",
                    start_date=p_start,
                    due_date=t_due,
                    project_id=new_project.id,
                    department=department or current_user.department,
                    creator_id=current_user.id
                )
                db.add(new_task)
            db.commit()
        except Exception as e:
            print(f"Error creating suggested tasks: {e}")

    return RedirectResponse(url="/projects", status_code=303)


@app.post("/projects/{project_id}/update", response_class=RedirectResponse)
def update_project(project_id: int,
                   name: str = Form(...), description: str = Form(None), 
                   start_date: str = Form(None), end_date: str = Form(None), 
                   status: str = Form(...),
                   department: str = Form(None),
                   assignee_ids: List[int] = Form([]),
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    """프로젝트 업데이트"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)

    s_date = utils.parse_date(start_date, "%Y-%m") if start_date else None
    e_date = utils.parse_date(end_date, "%Y-%m") if end_date else None
    
    # Department 처리: 빈 문자열을 None으로 변환
    department_value = department if department and department.strip() else None
    print(f"[DEBUG] Updating project {project_id}: department received = '{department}', processed = '{department_value}'")
    
    project.name = name
    project.description = description
    project.start_date = s_date
    project.end_date = e_date
    project.status = status
    project.department = department_value
    
    # 담당자 목록 전체 교체
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        project.assignees = users
    else:
        project.assignees = []
    
    db.commit()
    return RedirectResponse(url="/projects", status_code=303)


@app.get("/api/projects/{project_id}/tasks")
def get_project_tasks(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """프로젝트별 업무 목록 API"""
    if not current_user:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    
    data = []
    for t in tasks:
        assignees = [u.username for u in t.assignees]
        data.append({
            "id": t.id,
            "title": t.title,
            "description": t.description or "",
            "status": t.status,
            "department": t.department or "",
            "assignees": assignees,
            "assignee_ids": [u.id for u in t.assignees], 
            "assignees_str": ", ".join(assignees),
            "start_date": t.start_date.strftime("%Y-%m-%d") if t.start_date else None,
            "due_date": t.due_date.strftime("%Y-%m-%d") if t.due_date else None,
            "project_id": t.project_id,
            "filenames": [f.filename for f in t.files],
            "filepaths": [f.filepath for f in t.files],
            "progresses": [{
                "id": p.id,
                "content": p.content,
                "date": p.date.strftime("%Y-%m-%d") if p.date else "",
                "writer": p.writer.username if p.writer else "Unknown"
            } for p in t.progresses]
        })
        
    return JSONResponse(content=data)


@app.post("/projects/{project_id}/upload")
async def upload_file(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """프로젝트 파일 업로드"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return RedirectResponse(url="/projects", status_code=303)

    # 파일 검증
    file_content = await file.read()
    is_valid, error_msg = utils.validate_file_upload(file.filename, len(file_content))
    if not is_valid:
        return RedirectResponse(url=f"/projects?error={error_msg}", status_code=303)
    
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as buffer:
        buffer.write(file_content)

    new_file = models.ProjectFile(
        filename=file.filename,
        filepath=f"/uploads/{filename}",
        project_id=project_id
    )
    db.add(new_file)
    db.commit()

    return RedirectResponse(url="/projects", status_code=303)


@app.get("/tasks", response_class=HTMLResponse)
def read_tasks_page(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """업무 목록 페이지"""
    if not current_user:
        return RedirectResponse(url="/login")
    
    users = db.query(models.User).all()
    users = db.query(models.User).all()
    projects = db.query(models.Project).all()
    
    tasks_scheduled = db.query(models.Task).filter(models.Task.status == "Todo").all()
    tasks_inprogress = db.query(models.Task).filter(models.Task.status == "In Progress").all()
    tasks_done = db.query(models.Task).filter(models.Task.status == "Done").all()
    
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "user": current_user,
        "scheduled": tasks_scheduled,
        "inprogress": tasks_inprogress,
        "completed": tasks_done, 
        "users": users,
        "users": users,
        "projects": projects
    })

@app.get("/work-templates", response_class=HTMLResponse)
def read_work_templates_page(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """업무 템플릿 페이지"""
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Serialize Custom Templates for easy usage
    raw_templates = db.query(models.WorkTemplate).all()
    custom_templates_list = []
    
    import json # ensure json is imported or use existing
    
    for t in raw_templates:
        # Safe JSON parsing for phases
        phases_data = []
        try:
            if t.content_json:
                phases_data = json.loads(t.content_json)
        except:
            phases_data = []
            
        custom_templates_list.append({
            "id": t.id,
            "name": t.name,
            "category": t.category,
            "description": t.description,
            "phases": phases_data,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "editor": t.editor, # Relationship might be tricky for pure dict if we want to default render,
                                # but for the HTML loop we can stick to 'raw_templates' 
                                # OR just pass raw_templates for logic and this list for JS?
                                # Let's pass BOTH or just use raw for Jinja and Serializable for JS.
                                # But datetime and User objects are not JSON serializable easily.
            # Let's simplify: Pass raw_templates for the UI loop (it works fine with relationships).
            # Pass a separate 'custom_templates_json' list for the JS data variable.
            # We need to serialize datetimes and remove objects.
        })
        
    # Create a JSON-friendly structure for the JS variable
    js_templates = []
    for t in raw_templates:
        try:
            phases_obj = json.loads(t.content_json) if t.content_json else []
        except:
            phases_obj = []
            
        js_templates.append({
            "id": t.id,
            "name": t.name,
            "category": t.category,
            "description": t.description,
            "phases": phases_obj, # This is a dict/list
        })
        
    return templates.TemplateResponse("work_templates.html", {
        "request": request,
        "user": current_user,
        "templates": wbs_templates.TEMPLATES,
        "custom_templates": raw_templates,
        "custom_templates_data": js_templates
    })


@app.post("/tasks", response_class=RedirectResponse)
def create_task_page(request: Request, 
                title: str = Form(...), 
                description: str = Form(None),
                status: str = Form(...),
                assignee_ids: List[int] = Form([]),
                due_date: str = Form(None),
                project_id: int = Form(0),
                department: str = Form(None),
                db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    """업무 생성 (업무 페이지)"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    new_task = models.Task(
        title=title,
        description=description,
        status=status,
        due_date=utils.parse_date(due_date, '%Y-%m-%d'),
        project_id=None if project_id == 0 else project_id,
        department=department,
        creator_id=current_user.id
    )
    db.add(new_task)
    db.commit()
    
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        new_task.assignees = users
        if users:
            new_task.assignee_id = users[0].id
        db.commit()
    return RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/{task_id}/update", response_class=RedirectResponse)
def update_task_details(task_id: int,
                        title: str = Form(...),
                        description: str = Form(None),
                        status: str = Form(...),
                        assignee_ids: List[int] = Form([]),
                        start_date: str = Form(None),
                        due_date: str = Form(None),
                        project_id: int = Form(0),
                        department: str = Form(None),
                        progress_content: str = Form(None),
                        progress_date: str = Form(None),
                        db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    """업무 상세 정보 업데이트"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return RedirectResponse(url="/tasks", status_code=303)
    
    task.title = title
    task.description = description
    task.status = status
    
    # 담당자 업데이트
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        task.assignees = users
        if users:
            task.assignee_id = users[0].id
    else:
        task.assignees = []
        task.assignee_id = None

    task.start_date = utils.parse_date(start_date, '%Y-%m-%d')
    task.due_date = utils.parse_date(due_date, '%Y-%m-%d')
    task.project_id = None if project_id == 0 else project_id
    task.department = department
    
    # Progress Entry
    if progress_content and progress_content.strip():
        p_date = utils.parse_date(progress_date, '%Y-%m-%d')
        if not p_date:
            p_date = datetime.date.today()
            
        new_progress = models.TaskProgress(
            task_id=task.id,
            writer_id=current_user.id,
            content=progress_content,
            date=p_date
        )
        db.add(new_progress)

    db.commit()
    return RedirectResponse(url="/tasks", status_code=303)

@app.post("/tasks/{task_id}/upload", response_class=RedirectResponse)
async def upload_task_file(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """업무 파일 업로드"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return RedirectResponse(url="/tasks", status_code=303)
    
    # 파일 검증
    file_content = await file.read()
    is_valid, error_msg = utils.validate_file_upload(file.filename, len(file_content))
    if not is_valid:
        return RedirectResponse(url=f"/tasks?error={error_msg}", status_code=303)
    
    upload_dir = "uploads/tasks"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as buffer:
        buffer.write(file_content)
    
    task_file = models.TaskFile(
        filename=file.filename,
        filepath=f"/uploads/tasks/{filename}",
        task_id=task_id
    )
    db.add(task_file)
    db.commit()

    return RedirectResponse(url="/tasks", status_code=303)





@app.post("/projects/{project_id}/delete", response_class=RedirectResponse)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project:
        db.delete(project)
        db.commit()
    return RedirectResponse(url="/projects", status_code=303)

@app.post("/tasks/{task_id}/delete", response_class=RedirectResponse)
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
    # Check referer to redirect back to where we came from (dashboard or tasks page)
    referer = request.headers.get("referer")
    if referer and "tasks" not in referer: # If not from tasks page, assume dashboard or home
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/delete_bulk", response_class=RedirectResponse)
def delete_bulk_tasks(task_ids: List[int] = Form(...),
                      db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user)):
    """업무 일괄 삭제"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    if not task_ids:
        return RedirectResponse(url="/tasks", status_code=303)

    try:
        # 안전한 삭제를 위해 조회 후 삭제
        tasks = db.query(models.Task).filter(models.Task.id.in_(task_ids)).all()
        for t in tasks:
            # 권한 체크: 관리자, 작성자, 담당자만 삭제 가능
            can_delete = False
            if current_user.role == "admin":
                can_delete = True
            elif t.creator_id == current_user.id:
                can_delete = True
            elif t.assignee_id == current_user.id: # Legacy check
                can_delete = True
            else:
                # Multi-assignee check
                for assignee in t.assignees:
                    if assignee.id == current_user.id:
                        can_delete = True
                        break
            
            if can_delete:
                db.delete(t)
            else:
                print(f"[WARNING] User {current_user.username} tried to delete task {t.id} without permission")
            
        db.commit()
    except Exception as e:
        print(f"Bulk Delete Tasks Error: {e}")
        db.rollback()
        
    return RedirectResponse(url="/tasks", status_code=303)



# --- Meeting Minutes Routes ---

@app.get("/meeting_minutes", response_class=HTMLResponse)
def read_meeting_minutes(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login")
    
    minutes = db.query(models.MeetingMinutes).order_by(models.MeetingMinutes.date.desc()).all()
    
    return templates.TemplateResponse("meeting_minutes.html", {
        "request": request,
        "user": current_user,
        "minutes": minutes
    })

@app.post("/meeting_minutes", response_class=RedirectResponse)
async def create_meeting_minute(
                          topic: str = Form(...), 
                          date_str: str = Form(...),
                          time: str = Form(None),
                          location: str = Form(None),
                          attendees: str = Form(None),
                          content: str = Form(...),
                          tasks_data: str = Form(None), # JSON string of selected tasks
                          files: List[UploadFile] = File(None),
                          db: Session = Depends(get_db),
                          current_user: models.User = Depends(get_current_user)):
    """회의록 생성 및 업무 자동 등록"""
    print(f"[DEBUG] Raw POST Request. Topic: {topic}, User: {current_user}")
    try:
        # DEBUG LOGGING
        try:
            with open("debug_tasks.log", "a") as f:
                f.write(f"\n[{datetime.now()}] Create Meeting Request\n")
                f.write(f"Topic: {topic}\n")
                f.write(f"Tasks Data: {tasks_data}\n")
        except Exception as log_e:
            print(f"[ERROR] Failed to write debug log: {log_e}")
            
        if not current_user:
            print("[DEBUG] No current user, redirecting to login")
            return RedirectResponse(url="/login", status_code=303)
            
        m_date = utils.parse_date(date_str, "%Y-%m-%d")
        
        # 1. Create Meeting Minute
        # Fix: Model class name is MeetingMinutes (plural)
        new_minute = models.MeetingMinutes(
            topic=topic,
            date=m_date,
            time=time,
            location=location,
            attendees=attendees,
            content=content,
            writer_id=current_user.id
        )
        db.add(new_minute)
        db.commit()
        db.refresh(new_minute)
        
        # 2. Create Tasks (if any)
        if tasks_data and tasks_data.strip():
            log_path = os.path.abspath("debug_tasks.log")
            try:
                with open(log_path, "a") as f:
                    f.write(f"\n[{datetime.now()}] Processing Tasks Data: {tasks_data}\n")
                
                print(f"[DEBUG] Processing AI Tasks: {tasks_data}")
                import json
                from datetime import timedelta
                tasks_list = json.loads(tasks_data)
                
                with open(log_path, "a") as f:
                    f.write(f"Parsed JSON: {tasks_list}\n")

                for t in tasks_list:
                    # Find assignee
                    assignee_id = None
                    assignee_dept = None
                    if t.get("assignee_name"):
                        # Simple fuzzy match or exact match
                        u = db.query(models.User).filter(models.User.username == t["assignee_name"]).first()
                        if u: 
                            assignee_id = u.id
                            assignee_dept = u.department
                            with open(log_path, "a") as f:
                                f.write(f"Found Assignee: {u.username} (ID: {u.id})\n")
                        else:
                            with open(log_path, "a") as f:
                                f.write(f"Assignee not found: {t.get('assignee_name')}\n")
                    
                    # Use assignee's department if available, else creator's
                    dept = assignee_dept if assignee_dept else current_user.department

                    # Default due date logic
                    d_date = None
                    if t.get("due_date"):
                        d_date = utils.parse_date(t.get("due_date"), "%Y-%m-%d")
                    else:
                        d_date = m_date + timedelta(days=7)

                    new_task = models.Task(
                        title=t.get("title", "New Task"),
                        description=f"[From Meeting: {topic}] Auto-generated task.",
                        status="Todo",
                        due_date=d_date,
                        creator_id=current_user.id,
                        project_id=None, # No project link for now
                        department=dept
                    )
                    db.add(new_task)
                    db.flush() # to get ID
                    
                    with open(log_path, "a") as f:
                        f.write(f"Created Task ID: {new_task.id}, Title: {new_task.title}\n")

                    if assignee_id:
                        u = db.query(models.User).get(assignee_id)
                        new_task.assignees.append(u)
                        
                db.commit()
                print("[DEBUG] AI Tasks Created Successfully")
                with open(log_path, "a") as f:
                    f.write(f"[{datetime.now()}] All tasks committed successfully.\n")
                
            except Exception as e:
                print(f"[ERROR] Failed to create AI tasks: {e}")
                import traceback
                error_trace = traceback.format_exc()
                print(error_trace)
                try:
                    with open(log_path, "a") as f:
                        f.write(f"[ERROR] Exception: {e}\n{error_trace}\n")
                except:
                    pass
                # Don't fail the whole request, just log it


        # 파일 업로드 처리
        if files:
            upload_dir = "uploads/meeting_minutes"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            for file in files:
                if file.filename:
                    file_content = await file.read()
                    is_valid, error_msg = utils.validate_file_upload(file.filename, len(file_content))
                    if not is_valid:
                        continue  # 잘못된 파일은 건너뛰기
                    
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"{timestamp}_{file.filename}"
                    filepath = os.path.join(upload_dir, filename)
                    
                    with open(filepath, "wb") as buffer:
                        buffer.write(file_content)
                    
                    new_file = models.MeetingMinuteFile(
                        filename=file.filename,
                        filepath=f"/uploads/meeting_minutes/{filename}",
                        meeting_minute_id=new_minute.id
                    )
                    db.add(new_file)
            db.commit()
        
        return RedirectResponse(url="/meeting_minutes", status_code=303)
        
    except Exception as e:
        print(f"Meeting Minute Save Error: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"<h1>Internal Server Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", status_code=500)


@app.post("/meeting_minutes/delete_bulk", response_class=RedirectResponse)
def delete_bulk_minutes(minute_ids: List[int] = Form(...),
                       db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    """회의록 일괄 삭제"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    if not minute_ids:
        return RedirectResponse(url="/meeting_minutes", status_code=303)

    try:
        # 권한 확인: 관리자가 아니면 자신이 작성한 것만 삭제 가능하도록? 
        # 현재는 편의상 로그인한 유저는 삭제 가능하게 처리 (또는 필요시 로직 추가)
        # db.query(models.MeetingMinutes).filter(models.MeetingMinutes.id.in_(minute_ids)).delete(synchronize_session=False)
        
        # 안전한 삭제를 위해 조회 후 삭제 (파일 삭제 등 확장을 위해)
        minutes = db.query(models.MeetingMinutes).filter(models.MeetingMinutes.id.in_(minute_ids)).all()
        for m in minutes:
            # 권한 체크: 작성자 본인 또는 관리자만 삭제 가능
            if current_user.role != "admin" and m.writer_id != current_user.id:
                print(f"[WARNING] User {current_user.username} tried to delete minute {m.id} owned by {m.writer_id}")
                continue # Skip unauthorized
                
            db.delete(m)
            
        db.commit()
    except Exception as e:
        print(f"Bulk Delete Error: {e}")
        db.rollback()
        
    return RedirectResponse(url="/meeting_minutes", status_code=303)


@app.get("/meeting_minutes/{minute_id}", response_class=HTMLResponse)
def read_meeting_minute_detail(request: Request, minute_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login")
    
    minute = db.query(models.MeetingMinutes).filter(models.MeetingMinutes.id == minute_id).first()
    if not minute:
        return RedirectResponse(url="/meeting_minutes")
        
    return templates.TemplateResponse("meeting_minute_detail.html", {
        "request": request,
        "user": current_user,
        "minute": minute
    })

# --- Calendar Routes ---

@app.get("/calendar", response_class=HTMLResponse)
async def read_calendar(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """일정 관리 페이지"""
    if not current_user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("calendar.html", {"request": request, "user": current_user})

@app.get("/api/events")
def get_events(scope: str = "all", db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """일정 조회 API"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    query = db.query(models.Event)
    
    if scope == "personal":
        query = query.filter(models.Event.user_id == current_user.id)
    elif scope == "department":
        query = query.filter(models.Event.department == current_user.department)
    # scope == 'all' returns all events (or potentially limited to visibility rules if needed)
    
    events = query.all()
    
    # Format for FullCalendar
    formatted_events = []
    for event in events:
        formatted_events.append({
            "id": event.id,
            "title": event.title,
            "start": event.start_time.isoformat() if event.start_time else None,
            "end": event.end_time.isoformat() if event.end_time else None,
            "allDay": event.is_all_day,
            "description": event.description,
            "backgroundColor": "#3b82f6" if event.user_id == current_user.id else "#10b981", # Blue for mine, Green for others
            "borderColor": "#3b82f6" if event.user_id == current_user.id else "#10b981",
        })
    return formatted_events

@app.post("/api/events")
def create_event(
    title: str = Form(...),
    description: str = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...),
    is_all_day: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """일정 생성 API"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
    end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
    
    new_event = models.Event(
        title=title,
        description=description,
        start_time=start_dt,
        end_time=end_dt,
        is_all_day=is_all_day,
        user_id=current_user.id,
        department=current_user.department
    )
    db.add(new_event)
    db.commit()
    return {"status": "success"}

@app.put("/api/events/{event_id}")
def update_event(
    event_id: int,
    title: str = Form(...),
    description: str = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...),
    is_all_day: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """일정 수정 API"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Permission check: Only creator or admin can update
    if event.user_id != current_user.id and current_user.role != 'admin':
         raise HTTPException(status_code=403, detail="Not authorized to update this event")

    start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
    end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
    
    event.title = title
    event.description = description
    event.start_time = start_dt
    event.end_time = end_dt
    event.is_all_day = is_all_day
    
    db.commit()
    return {"status": "success"}

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """일정 삭제 API"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Permission check: Only creator or admin can delete
    if event.user_id != current_user.id and current_user.role != 'admin':
         raise HTTPException(status_code=403, detail="Not authorized to delete this event")
         
    db.delete(event)
    db.commit()
    return {"status": "success"}

# --- AI Task Creation Routes ---

# --- AI Helper & Routes ---

class AIHelper:
    def __init__(self):
        if not config.GEMINI_API_KEY:
             raise Exception("No AI API Key configured")
        genai.configure(api_key=config.GEMINI_API_KEY)
        # Use gemini-flash-latest (as 1.5-flash specific alias was not found)
        self.model = genai.GenerativeModel(
            'gemini-flash-latest',
            generation_config={"response_mime_type": "application/json"}
        )

    def generate_task_json(self, text, user_context, project_context):
        prompt = f"""
        You are a project management assistant. Extract task details.
        
        Current Date: {date.today()}
        Users: {user_context}
        Projects: {project_context}
        User Input: "{text}"
        
        Output Schema (JSON):
        {{
            "title": "string",
            "description": "string",
            "due_date": "YYYY-MM-DD" or null,
            "assignee_ids": [int],
            "project_id": int or 0,
            "department": "string" or null
        }}
        """
        response = self.model.generate_content(prompt)
        return json.loads(response.text)

    def generate_event_action_json(self, text, user_context, event_context):
        prompt = f"""
        You are a calendar assistant. Determine if the user wants to CREATE, UPDATE, or DELETE an event.
        
        Current Date: {date.today()}
        Users: {user_context}
        Upcoming Events: {event_context}
        User Input: "{text}"
        
        Output Schema (JSON):
        {{
            "action": "CREATE" | "UPDATE" | "DELETE",
            "event_ids": [int] (Required for UPDATE/DELETE. If multiple match, list all.),
            "payload": {{
                "title": "string",
                "description": "string",
                "start_time": "YYYY-MM-DDTHH:MM:SS",
                "end_time": "YYYY-MM-DDTHH:MM:SS" or null
            }}
        }}
        """
        response = self.model.generate_content(prompt)
        return json.loads(response.text)

    def analyze_meeting_minutes(self, text, user_context):
        prompt = f"""
        You are a professional meeting secretary. Analyze the following meeting notes.
        
        IMPORTANT: All output (summary, decisions, risks, tasks) MUST be in KOREAN (한국어).

        Current Date: {date.today()}
        Participants Context: {user_context}
        Raw Notes:
        "{text}"

        Tasks:
        1. Summarize the meeting (5 bullet points max) in Korean.
        2. Extract key decisions (Decisions) in Korean.
        3. Identify risks or dependencies (Risks) in Korean.
        4. Extract actionable tasks (Action Items) in Korean. Try to match assignees from the context.

        Output Schema (JSON):
        {{
            "summary": "string (markdown bullet points)",
            "decisions": ["string"],
            "risks": ["string"],
            "action_items": [
                {{
                    "title": "string",
                    "assignee_name": "string (or null)",
                    "due_date": "YYYY-MM-DD" (or null),
                    "priority": "High" | "Normal" | "Low"
                }}
            ]
        }}
        """
        response = self.model.generate_content(prompt)
        return json.loads(response.text)



    def generate_wbs_json(self, goal, deadline, p_type, scope, stakeholders):
        prompt = f"""
        You are a project management expert. Create a WBS (Work Breakdown Structure) for a new project.
        
        Project Details:
        - Goal/Deliverables: {goal}
        - Deadline: {deadline}
        - Type: {p_type}
        - Scope: {scope}
        - Stakeholders: {stakeholders}
        - Current Date: {date.today()}

        Task:
        - Break down the project into standard phases: Planning, Preparation, Execution, Verification/Launch, Operation/Review.
        - Create specific tasks for each phase.
        - For each task, include a short checklist of sub-items.
        
        Output Schema (JSON):
        {{
            "phases": [
                {{
                    "phase_name": "string (e.g., Planning, Execution)",
                    "tasks": [
                        {{
                            "title": "string (Action-oriented task name)",
                            "checklist": ["string", "string"],
                            "estimated_days": int,
                            "is_milestone": boolean,
                            "is_core": boolean (true if essential, false if optional)
                        }}
                    ]
                }}
            ]
        }}
        """
        # Retry logic for 429 errors
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return json.loads(response.text)
            except Exception as e:
                is_rate_limit = "429" in str(e) or "ResourceExhausted" in str(e)
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"AI Rate Limit hit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                else:
                    raise e
    
    def generate_template_json(self, topic):
        prompt = f"""
        You are a process improvement expert. Create a new Work Template for the following topic:
        Topic: "{topic}"
        
        The template should follow the standard structure with Phases and Tasks.
        Language: KOREAN (한국어) - Titles and descriptions must be in Korean.
        
        Output Schema (JSON):
        {{
            "name": "string (Template Name)",
            "category": "string (Category Name e.g. 'Marketing', 'Development', 'HR')",
            "description": "string (Brief description of this process)",
            "phases": [
                {{
                    "phase_name": "string (e.g., 기획, 실행, 검토)",
                    "tasks": [
                        {{
                            "title": "string",
                            "description": "string",
                            "estimated_days": int,
                            "is_core": boolean,
                            "checklist": ["string", "string"]
                        }}
                    ]
                }}
            ]
        }}
        """
        response = self.model.generate_content(prompt)
        return json.loads(response.text)


@app.post("/api/projects/ai-wbs")
async def generate_project_wbs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """AI Project WBS Generation Endpoint"""
    try:
        data = await request.json()
        goal = data.get("goal")
        deadline = data.get("deadline")
        p_type = data.get("type")
        scope = data.get("scope")
        stakeholders = data.get("stakeholders")
        
        if not goal:
            raise HTTPException(status_code=400, detail="Project goal is required")
            
        ai = AIHelper()
        result = ai.generate_wbs_json(goal, deadline, p_type, scope, stakeholders)
        return result
    except Exception as e:
        print(f"AI WBS Error: {e}")
        status_code = 500
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.post("/api/work-templates/generate")
async def generate_work_template_api(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    """AI로 새 업무 템플릿 생성"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    try:
        data = await request.json()
        topic = data.get("topic")
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
            
        ai = AIHelper()
        result = ai.generate_template_json(topic)
        return result
    except Exception as e:
        print(f"Template Gen Error: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/work-templates")
async def create_work_template(
    name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    content_json: str = Form(...), # JSON string of phases
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """새 템플릿 저장"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
        
    new_template = models.WorkTemplate(
        name=name,
        category=category,
        description=description,
        content_json=content_json,
        creator_id=current_user.id
    )
    db.add(new_template)
    db.commit()
    
    return RedirectResponse(url="/work-templates", status_code=303)


@app.post("/work-templates/{template_id}/update")
async def update_work_template(
    template_id: int,
    name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    content_json: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """템플릿 수정"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
        
    template = db.query(models.WorkTemplate).filter(models.WorkTemplate.id == template_id).first()
    if not template:
        # Should probably return error page or alert, but redirecting for now
        return RedirectResponse(url="/work-templates?error=TemplateNotFound", status_code=303)
        
    template.name = name
    template.category = category
    template.description = description
    template.content_json = content_json
    template.updated_at = datetime.now()
    template.editor_id = current_user.id
    
    db.commit()
    
    return RedirectResponse(url="/work-templates", status_code=303)




@app.get("/api/projects/templates")
def get_wbs_templates():
    """Available WBS Templates List"""
    return [
        {
            "key": key, 
            "name": val["name"], 
            "description": val["description"],
            "category": val.get("category", "Other") 
        }
        for key, val in wbs_templates.TEMPLATES.items()
    ]

@app.get("/api/projects/templates/{key}")
def get_wbs_template_detail(key: str):
    """Get specific WBS template data"""
    if key not in wbs_templates.TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    return wbs_templates.TEMPLATES[key]


@app.post("/api/minutes/ai-analyze")
async def analyze_minutes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """AI Meeting Analysis Endpoint"""
    try:
        data = await request.json()
        text = data.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        users = db.query(models.User).all()
        user_ctx = ", ".join([f"{u.username}" for u in users])
        
        ai = AIHelper()
        result = ai.analyze_meeting_minutes(text, user_ctx)
        return result
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.post("/api/tasks/ai")
async def create_task_from_ai(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """AI를 이용한 자연어 업무 등록 (Structured Output 적용)"""
    try:
        data = await request.json()
        user_text = data.get("text")
        if not user_text:
            raise HTTPException(status_code=400, detail="No text provided")

        # Context fetching
        users = db.query(models.User).all()
        projects = db.query(models.Project).all()
        user_ctx = ", ".join([f"{u.username}(ID:{u.id})" for u in users])
        project_ctx = ", ".join([f"{p.name}(ID:{p.id})" for p in projects])

        # Generate JSON
        ai = AIHelper()
        task_data = ai.generate_task_json(user_text, user_ctx, project_ctx)
        
        # Logic to create task (reuse previous logic)
        dept = task_data.get('department') or current_user.department
        
        new_task = models.Task(
            title=task_data.get('title', 'New Task'),
            description=task_data.get('description'),
            status="Todo",
            start_date=date.today(),
            due_date=utils.parse_date(task_data.get('due_date'), "%Y-%m-%d") if task_data.get('due_date') else None,
            project_id=task_data.get('project_id', 0),
            department=dept,
            creator_id=current_user.id
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # Assignees
        a_ids = task_data.get('assignee_ids', [])
        if a_ids:
            for uid in a_ids:
                u = db.query(models.User).get(uid)
                if u: new_task.assignees.append(u)
            db.commit()

        return {"status": "success", "task_id": new_task.id}
    except Exception as e:
        print(f"AI Task Error: {e}")
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")


@app.post("/api/events/ai")
async def process_event_from_ai(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """AI를 이용한 일정 생성/수정/삭제"""
    try:
        data = await request.json()
        user_text = data.get("text")
        if not user_text: raise HTTPException(status_code=400, detail="No text provided")

        # Context: Fetch upcoming events (e.g., next 30 days) to allow update/delete
        # Also need users to map 'meeting with X'
        users = db.query(models.User).all()
        user_ctx = ", ".join([f"{u.username}(ID:{u.id})" for u in users])

        upcoming_events = db.query(models.Event).filter(
            models.Event.start_time >= (datetime.now() - timedelta(days=1)) # Include recently passed events too for context
        ).limit(30).all()
        
        event_ctx_list = []
        for e in upcoming_events:
            event_ctx_list.append(f"ID:{e.id}|Title:{e.title}|Time:{e.start_time}")
        event_ctx = "\n".join(event_ctx_list)

        ai = AIHelper()
        result = ai.generate_event_action_json(user_text, user_ctx, event_ctx)
        
        action = result.get('action')
        payload = result.get('payload', {})
        target_ids = result.get('event_ids', [])
        
        # Legacy support if AI returns single event_id
        if not target_ids and result.get('event_id'):
            target_ids = [result.get('event_id')]

        if action == "CREATE":
            start_str = payload.get('start_time')
            # Default to now if not provided (shouldn't happen with AI)
            start_dt = datetime.fromisoformat(start_str) if start_str else datetime.now()
            # If no end time, default to +1 hour
            end_str = payload.get('end_time')
            end_dt = datetime.fromisoformat(end_str) if end_str else (start_dt + timedelta(hours=1))

            new_event = models.Event(
                title=payload.get('title', 'New Event'),
                description=payload.get('description'),
                start_time=start_dt,
                end_time=end_dt,
                user_id=current_user.id,
                department=current_user.department
            )
            db.add(new_event)
            db.commit()
            return {"status": "success", "action": "CREATE", "count": 1}

        elif action == "UPDATE":
            if not target_ids:
                return {"status": "error", "message": "No event identified to update"}
            
            # Update all matched events (usually 1, but technically can be multiple)
            count = 0
            for tid in target_ids:
                event = db.query(models.Event).filter(models.Event.id == tid).first()
                if event and (event.user_id == current_user.id or current_user.role == 'admin'):
                    if payload.get('title'): event.title = payload['title']
                    if payload.get('description'): event.description = payload['description']
                    if payload.get('start_time'): event.start_time = datetime.fromisoformat(payload['start_time'])
                    if payload.get('end_time'): event.end_time = datetime.fromisoformat(payload['end_time'])
                    count += 1
            db.commit()
            return {"status": "success", "action": "UPDATE", "count": count}

        elif action == "DELETE":
            if not target_ids:
                return {"status": "error", "message": "No event identified to delete"}
            
            count = 0
            for tid in target_ids:
                event = db.query(models.Event).filter(models.Event.id == tid).first()
                if event and (event.user_id == current_user.id or current_user.role == 'admin'):
                    db.delete(event)
                    count += 1
            db.commit()
            return {"status": "success", "action": "DELETE", "count": count}

        else:
            return {"status": "error", "message": "Unknown action"}

    except Exception as e:
        print(f"AI Event Error: {e}")
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.get("/api/ai/test")
async def test_ai_connection():
    """Test AI connectivity and List Models"""
    try:
        if not config.GEMINI_API_KEY:
            return {"status": "error", "message": "API Key is missing in config"}
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                
        return {
            "status": "success", 
            "available_models": available_models, 
            "key_masked": config.GEMINI_API_KEY[:5] + "..."
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "type": str(type(e))}
