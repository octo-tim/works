from fastapi import FastAPI, Depends, Request, Form, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from typing import Optional
from datetime import date, datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-very-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 400

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    return user


try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Startup DB Error: {e}")
    # We continue, so the app starts and can show the error on request


app = FastAPI()

# Add JSONResponse import if not present, but using HTMLResponse for user visibility
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = "".join(traceback.format_exception(None, exc, exc.__traceback__))
    print(f"Global Error: {error_msg}")
    return HTMLResponse(
        status_code=500,
        content=f"<h1>Internal Server Error</h1><pre>{error_msg}</pre>"
    )

app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dummy Data Generator
def populate_db(db: Session):
    # 1. Admin Creation (Always ensure Admin exists and has correct password)
    admin_user = db.query(models.User).filter(models.User.username == "윤경식").first()
    if not admin_user:
        admin_user = models.User(
            username="윤경식", 
            password_hash=get_password_hash("k0349001!"),
            department="System",
            role="admin"
        )
        db.add(admin_user)
        db.commit()
    else:
        # Ensure password is correct even if user exists
        admin_user.password_hash = get_password_hash("k0349001!")
        db.commit()

    # 2. Check if Dummy Data Exists (Prevent duplicate dummy data)
    # Check for a known dummy user like 'Kim Manager'
    if db.query(models.User).filter(models.User.username == "Kim Manager").first():
        return

    # Users
    user1 = models.User(username="Kim Manager")
    user2 = models.User(username="Lee Designer")
    db.add_all([user1, user2])
    db.commit()

    # Clients
    client1 = models.Client(name="Samsung Electronics", contact_info="02-1234-5678")
    client2 = models.Client(name="Naver", contact_info="031-1234-5678")
    db.add_all([client1, client2])
    db.commit()

    # Categories
    cat1 = models.Category(name="Development", color="#3B82F6") # Blue
    cat2 = models.Category(name="Design", color="#EC4899") # Pink
    cat3 = models.Category(name="Meeting", color="#10B981") # Green
    db.add_all([cat1, cat2, cat3])
    db.commit()

    # Projects
    proj1 = models.Project(name="Website Redesign", description="Renewal project", start_date=date(2023, 10, 1), end_date=date(2023, 12, 31), status="In Progress", client_id=client1.id)
    proj2 = models.Project(name="Mobile App MVP", description="MVP development", start_date=date(2023, 11, 1), end_date=date(2024, 1, 31), status="Scheduled", client_id=client2.id)
    db.add_all([proj1, proj2])
    db.commit()

    # Tasks
    task1 = models.Task(title="Design Mockup", status="Done", due_date=date(2023, 10, 15), project_id=proj1.id, assignee_id=user2.id, category_id=cat2.id)
    task2 = models.Task(title="Frontend Setup", status="In Progress", due_date=date(2023, 10, 20), project_id=proj1.id, assignee_id=user1.id, category_id=cat1.id)
    task3 = models.Task(title="API Specs", status="Todo", due_date=date(2023, 10, 25), project_id=proj2.id, assignee_id=user1.id, category_id=cat1.id)
    task4 = models.Task(title="Client Meeting", status="Todo", due_date=date(2023, 10, 12), project_id=None, assignee_id=user1.id, category_id=cat3.id) # Inbox
    db.add_all([task1, task2, task3, task4])
    db.commit()

@app.on_event("startup")
def startup_event():
    try:
        db = SessionLocal()
        try:
            populate_db(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Startup Population Error: {e}")

# --- Debug Route (Remove later) ---
@app.get("/reset_admin", response_class=HTMLResponse)
def reset_admin(db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == "윤경식").first()
    msg = ""
    if not user:
        user = models.User(
            username="윤경식", 
            password_hash=get_password_hash("k0349001!"),
            department="System",
            role="admin"
        )
        db.add(user)
        msg = "Admin user created."
    else:
        user.password_hash = get_password_hash("k0349001!")
        msg = "Admin password updated to 'k0349001!'"
    
    db.commit()
    return f"Done: {msg} <a href='/login'>Go to Login</a>"

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
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(request: Request, username: str = Form(...), password: str = Form(...), department: str = Form(...), db: Session = Depends(get_db)):
    try:
        if db.query(models.User).filter(models.User.username == username).first():
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Username already exists"})
        
        new_user = models.User(
            username=username,
            password_hash=get_password_hash(password),
            department=department,
            role="admin" if username == "윤경식" else "user"
        )
        db.add(new_user)
        db.commit()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        print(f"Signup Error: {e}") # Log to server console
        return templates.TemplateResponse("signup.html", {"request": request, "error": f"Signup failed: {str(e)}"})

@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, 
              assignee_id: Optional[int] = None, 
              client_id: Optional[int] = None, 
              category_id: Optional[int] = None,
              target_month: Optional[int] = None,
              db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Default to current month if not specified
    if target_month is None:
        target_month = datetime.now().month
    
    query = db.query(models.Task)
    
    # Dept Permission: Regular users only see tasks assigned to them? Or tasks in their dept?
    # Requirement: "사용자는 자기 부서 업무만 볼수 있도록 한다." (Users see only their dept's work)
    # Tasks don't have direct Dept field, but Assignee does.
    # So filter tasks where assignee.department == current_user.department
    if current_user.role != "admin":
        if current_user.department == "System":
             # Show tasks assigned to System dept users
             query = query.join(models.User).filter(models.User.department == "System")
        elif current_user.department == "Distribution":
             query = query.join(models.User).filter(models.User.department == "Distribution")
        # Else?
    
    if assignee_id:
        query = query.filter(models.Task.assignee_id == assignee_id)

    if category_id:
        query = query.filter(models.Task.category_id == category_id)
    if client_id:
        # Filter tasks by client via project
        query = query.join(models.Project).filter(models.Project.client_id == client_id)
        # Note: This will exclude Inbox tasks (project_id=None). 
        # If we want to include inbox tasks that are somehow related to client (impossible with current schema), we'd need a different approach.
        # But per schema, inbox tasks have no project, thus no client.

    tasks = query.all()

    # Organized for Kanban
    tasks_todo = [t for t in tasks if t.status == 'Todo']
    tasks_inprogress = [t for t in tasks if t.status == 'In Progress']
    tasks_done = [t for t in tasks if t.status == 'Done']

    users = db.query(models.User).all()
    clients = db.query(models.Client).all()
    categories = db.query(models.Category).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "tasks_todo": tasks_todo,
        "tasks_inprogress": tasks_inprogress,
        "tasks_done": tasks_done,
        "users": users,
        "clients": clients,
        "categories": categories,
        "projects": db.query(models.Project).all(), # Pass projects for modal
        "selected_assignee": assignee_id,
        "selected_client": client_id,
        "selected_category": category_id,
        "selected_month": target_month,
        "goals": {
            "annual_2026": db.query(models.AnnualGoal).filter(models.AnnualGoal.year == 2026).first(),
            "monthly_obj_system": db.query(models.MonthlyObjective).filter(models.MonthlyObjective.year == 2026, models.MonthlyObjective.month == target_month, models.MonthlyObjective.division == 'System').first(),
            "monthly_obj_dist": db.query(models.MonthlyObjective).filter(models.MonthlyObjective.year == 2026, models.MonthlyObjective.month == target_month, models.MonthlyObjective.division == 'Distribution').first(),
            "monthly_perf_system": db.query(models.MonthlyPerformance).filter(models.MonthlyPerformance.year == 2026, models.MonthlyPerformance.month == target_month, models.MonthlyPerformance.division == 'System').first(),
            "monthly_perf_dist": db.query(models.MonthlyPerformance).filter(models.MonthlyPerformance.year == 2026, models.MonthlyPerformance.month == target_month, models.MonthlyPerformance.division == 'Distribution').first()
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
@app.get("/octovision", response_class=HTMLResponse)
def read_octovision(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login")
    # Helper to safe convert string to int/float for summing
    def safe_float(val):
        try:
            return float(val.replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0

    perf_sys = db.query(models.MonthlyPerformance).filter(models.MonthlyPerformance.year == 2026, models.MonthlyPerformance.division == 'System').all()
    perf_dist = db.query(models.MonthlyPerformance).filter(models.MonthlyPerformance.year == 2026, models.MonthlyPerformance.division == 'Distribution').all()
    
    # Calculate Totals
    total_goal_sys = sum(safe_float(p.goal_value) for p in perf_sys)
    total_actual_sys = sum(safe_float(p.actual_value) for p in perf_sys)
    total_goal_dist = sum(safe_float(p.goal_value) for p in perf_dist)
    total_actual_dist = sum(safe_float(p.actual_value) for p in perf_dist)

    # Format totals back to string (optional: int if no decimals)
    total_goal_sys_str = f"{int(total_goal_sys):,}" 
    total_actual_sys_str = f"{int(total_actual_sys):,}"
    total_goal_dist_str = f"{int(total_goal_dist):,}"
    total_actual_dist_str = f"{int(total_actual_dist):,}"

    return templates.TemplateResponse("octovision.html", {
        "request": request,
        "user": current_user,
        "goals": {
            "annual_2026": db.query(models.AnnualGoal).filter(models.AnnualGoal.year == 2026).first(),
            "objectives_system": {g.month: g.content for g in db.query(models.MonthlyObjective).filter(models.MonthlyObjective.year == 2026, models.MonthlyObjective.division == 'System').all()},
            "objectives_dist": {g.month: g.content for g in db.query(models.MonthlyObjective).filter(models.MonthlyObjective.year == 2026, models.MonthlyObjective.division == 'Distribution').all()},
            "performance_system": {g.month: g for g in perf_sys},
            "performance_dist": {g.month: g for g in perf_dist},
            "totals": {
                "sys_goal": total_goal_sys_str,
                "sys_actual": total_actual_sys_str,
                "dist_goal": total_goal_dist_str,
                "dist_actual": total_actual_dist_str
            },
            # Group schedules by month
            "schedules_system": group_schedules_by_month(db.query(models.KeySchedule).filter(models.KeySchedule.division == 'System').all()),
            "schedules_dist": group_schedules_by_month(db.query(models.KeySchedule).filter(models.KeySchedule.division == 'Distribution').all())
        }
    })

def group_schedules_by_month(schedules):
    grouped = {}
    for s in schedules:
        if s.date.year == 2026:
            if s.date.month not in grouped:
                grouped[s.date.month] = []
            grouped[s.date.month].append(s)
    # Sort by date
    for m in grouped:
        grouped[m].sort(key=lambda x: x.date)
    return grouped

@app.post("/goals/schedule", response_class=RedirectResponse)
def update_key_schedule(request: Request, date_str: str = Form(...), division: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    # date_str is expected to be YYYY-MM-DD from input
    sched_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # We create a new entry for every input. Or do we update distinct ones? 
    # Since it's a list of schedules, and UI might just append. 
    # For now, let's just ADD new one.
    schedule = models.KeySchedule(date=sched_date, division=division, content=content)
    db.add(schedule)
    db.commit()
    return RedirectResponse(url=request.headers.get("referer"), status_code=303)

@app.post("/tasks/create", response_class=RedirectResponse)
def create_task(title: str = Form(...), 
                description: str = Form(None),
                status: str = Form("Todo"),
                start_date: str = Form(None),
                due_date: str = Form(None),
                project_id: int = Form(None),
                assignee_id: int = Form(None),
                category_id: int = Form(None),
                db: Session = Depends(get_db)):
    
    date_obj = None
    start_date_obj = None
    if due_date:
        date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()

    if project_id == 0: project_id = None
    if assignee_id == 0: assignee_id = None
    if category_id == 0: category_id = None

    new_task = models.Task(
        title=title,
        description=description,
        status=status,
        start_date=start_date_obj,
        due_date=date_obj,
        project_id=project_id,
        assignee_id=assignee_id,
        category_id=category_id
    )
    db.add(new_task)
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tasks/update_status/{task_id}")
@app.post("/tasks/update_status/{task_id}")
def update_task_status(task_id: int, status: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.status = status
        db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
def read_admin(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login")
    users = db.query(models.User).all()
    clients = db.query(models.Client).all()
    categories = db.query(models.Category).all()
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "user": current_user,
        "users": users, 
        "clients": clients, 
        "categories": categories
    })

@app.post("/admin/users", response_class=RedirectResponse)
@app.post("/admin/users", response_class=RedirectResponse)
def create_user(username: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    db.add(models.User(username=username))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/clients", response_class=RedirectResponse)
@app.post("/admin/clients", response_class=RedirectResponse)
def create_client(name: str = Form(...), contact_info: str = Form(None), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    db.add(models.Client(name=name, contact_info=contact_info))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/categories", response_class=RedirectResponse)
@app.post("/admin/categories", response_class=RedirectResponse)
def create_category(name: str = Form(...), color: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    db.add(models.Category(name=name, color=color))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/projects", response_class=HTMLResponse)
@app.get("/projects", response_class=HTMLResponse)
def read_projects(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login")
    # Group projects by status
    projects = db.query(models.Project).all()
    scheduled = [p for p in projects if p.status == 'Scheduled' or p.status == '예정'] 
    # Handling both English/Korean in case db was populated differently or previous data exists. 
    # For now ensuring defaults are English or Korean as User decided.
    # The requirement said "예정. 진행. 완료로 구분". I will use these strings for display or standard Enum.
    # Let's align with the Korean UI request. I will stick to "Scheduled", "In Progress", "Completed" internally for consistency or just use Korean?
    # The user asked: "예정. 진행. 완료로 구분하여 볼수 있도록 구성".
    # I'll use English internally "Scheduled", "In Progress", "Completed" but display mapping in template.
    
    # Actually, in populate_db I used "Scheduled", "In Progress". 
    scheduled = [p for p in projects if p.status == 'Scheduled']
    inprogress = [p for p in projects if p.status == 'In Progress']
    completed = [p for p in projects if p.status == 'Completed']
    
    clients = db.query(models.Client).all()

    return templates.TemplateResponse("projects.html", {
        "request": request,
        "user": current_user,
        "scheduled": scheduled, 
        "inprogress": inprogress, 
        "completed": completed,
        "clients": clients
    })

@app.post("/projects", response_class=RedirectResponse)
def create_project(name: str = Form(...), description: str = Form(None), 
                   start_date: str = Form(None), end_date: str = Form(None), 
                   status: str = Form(...), client_id: int = Form(None),
                   db: Session = Depends(get_db)):
    
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    if client_id == 0: client_id = None

    new_project = models.Project(
        name=name, 
        description=description, 
        start_date=s_date, 
        end_date=e_date, 
        status=status, 
        client_id=client_id
    )
    db.add(new_project)
    db.commit()
    return RedirectResponse(url="/projects", status_code=303)


@app.post("/projects/{project_id}/update", response_class=RedirectResponse)
def update_project(project_id: int,
                   name: str = Form(...), description: str = Form(None), 
                   start_date: str = Form(None), end_date: str = Form(None), 
                   status: str = Form(...), client_id: int = Form(None),
                   db: Session = Depends(get_db)):
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
         return RedirectResponse(url="/projects", status_code=303)

    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    if client_id == 0: client_id = None

    project.name = name
    project.description = description
    project.start_date = s_date
    project.end_date = e_date
    project.status = status
    project.client_id = client_id
    
    db.commit()
    return RedirectResponse(url="/projects", status_code=303)


@app.post("/projects/{project_id}/upload")
@app.post("/projects/{project_id}/upload")
def upload_file(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
         return RedirectResponse(url="/projects", status_code=303)

    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Prevent overwriting or collision by simple logic (or just UUID, but let's keep name for simplicity and risk override)
    # Or better, prepend timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_file = models.ProjectFile(
        filename=file.filename,
        filepath=f"/uploads/{filename}",
        project_id=project_id
    )
    db.add(new_file)
    db.commit()

    return RedirectResponse(url="/projects", status_code=303)


@app.get("/tasks", response_class=HTMLResponse)
@app.get("/tasks", response_class=HTMLResponse)
def read_tasks_page(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login")
    users = db.query(models.User).all()
    categories = db.query(models.Category).all()
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
        "categories": categories,
        "projects": projects
    })

@app.post("/tasks", response_class=RedirectResponse)
def create_task_page(request: Request, 
                title: str = Form(...), 
                description: str = Form(None),
                status: str = Form(...),
                assignee_id: int = Form(0),
                due_date: str = Form(None),
                project_id: int = Form(0),
                category_id: int = Form(0),
                db: Session = Depends(get_db)):
    
    new_task = models.Task(
        title=title,
        description=description,
        status=status,
        due_date=datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None,
        assignee_id=assignee_id if assignee_id != 0 else None,
        project_id=project_id if project_id != 0 else None,
        category_id=category_id if category_id != 0 else None
    )
    db.add(new_task)
    db.commit()
    return RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/{task_id}/update", response_class=RedirectResponse)
def update_task_details(task_id: int,
                        title: str = Form(...),
                        description: str = Form(None),
                        status: str = Form(...),
                        assignee_id: int = Form(0),
                        start_date: str = Form(None),
                        due_date: str = Form(None),
                        project_id: int = Form(0),
                        category_id: int = Form(0),
                        db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.title = title
        task.description = description
        task.status = status
        task.assignee_id = assignee_id if assignee_id != 0 else None
        task.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        task.project_id = project_id if project_id != 0 else None
        task.category_id = category_id if category_id != 0 else None
        db.commit()
    return RedirectResponse(url="/tasks", status_code=303)

@app.post("/tasks/{task_id}/upload", response_class=RedirectResponse)
@app.post("/tasks/{task_id}/upload", response_class=RedirectResponse)
async def upload_task_file(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    upload_dir = "uploads/tasks"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    task_file = models.TaskFile(
        filename=file.filename,
        filepath=f"/uploads/tasks/{filename}",
        task_id=task_id
    )
    db.add(task_file)
    db.commit()
    return RedirectResponse(url="/tasks", status_code=303)
