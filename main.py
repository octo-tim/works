from fastapi import FastAPI, Depends, Request, Form, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from typing import Optional, List
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
    # SAMPLE DATA REMOVED: Users and Clients will be created manually or via admin panel.
    return

@app.on_event("startup")
def on_startup():
    print("DEBUG: SERVER STARTING - VERIFYING VERSION v1")
    try:
        db = SessionLocal()
        try:
            # Migration: Check for 'creator_id' in projects and tasks
            from sqlalchemy import text
            try:
                # Check Project
                db.execute(text("SELECT creator_id FROM projects LIMIT 1"))
            except Exception:
                db.rollback()
                print("Migrating: Adding creator_id to projects")
                db.execute(text("ALTER TABLE projects ADD COLUMN creator_id INTEGER REFERENCES users(id)"))
                db.commit()
            
            try:
                # Check Task
                db.execute(text("SELECT creator_id FROM tasks LIMIT 1"))
            except Exception:
                db.rollback()
                print("Migrating: Adding creator_id to tasks")
                db.execute(text("ALTER TABLE tasks ADD COLUMN creator_id INTEGER REFERENCES users(id)"))
                db.commit()
            
            try:
                # Migration: Add columns blindly (Ignore if exists)
                # This works for both SQLite and Postgres (Postgres throws generic error if exists)
                columns_to_add = ["email", "phone", "position"]
                for col in columns_to_add:
                    try:
                        db.execute(text(f"ALTER TABLE users ADD COLUMN {col} VARCHAR"))
                        db.commit()
                        print(f"Migrating: Added {col} to users")
                    except Exception as e:
                        db.rollback()
                        # print(f"Migrating: {col} likely exists or error: {e}")
                        pass
                
                # Migration: Translate Department Names
                # users
                db.execute(text("UPDATE users SET department = '시스템사업부' WHERE department = 'System'"))
                db.execute(text("UPDATE users SET department = '유통사업부' WHERE department = 'Distribution'"))
                db.execute(text("UPDATE users SET department = '경영지원팀' WHERE department = 'Management'"))
                
                # projects
                db.execute(text("UPDATE projects SET department = '시스템사업부' WHERE department = 'System'"))
                db.execute(text("UPDATE projects SET department = '유통사업부' WHERE department = 'Distribution'"))
                db.execute(text("UPDATE projects SET department = '경영지원팀' WHERE department = 'Management'"))
                
                # tasks
                db.execute(text("UPDATE tasks SET department = '시스템사업부' WHERE department = 'System'"))
                db.execute(text("UPDATE tasks SET department = '유통사업부' WHERE department = 'Distribution'"))
                db.execute(text("UPDATE tasks SET department = '경영지원팀' WHERE department = 'Management'"))

                db.commit()
            except Exception as e:
                print(f"Migration Error (Users/Dept): {e}")
                db.rollback()

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
              assignee_id: Optional[str] = None, 
              category_id: Optional[str] = None,
              department: Optional[str] = None, 
              target_month: Optional[int] = None,
              db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    
    if not current_user:
        return RedirectResponse(url="/login")
    
    # Default to current month if not specified
    if target_month is None:
        target_month = datetime.now().month
    
    query = db.query(models.Task)
    
    # Department Filtering Logic
    if current_user.role == "admin":
        if department:
             query = query.join(models.User).filter(models.User.department == department)
        # If no department selected, show all (Admin privilege)
    else:
        # Regular users: Force filter by their own department
        # Ignore the 'department' query param if provided (security)
        department = current_user.department # For UI reflection if needed, or just force query
        query = query.join(models.User).filter(models.User.department == current_user.department)
    
    # Handle int conversion for empty strings
    a_id = int(assignee_id) if assignee_id and assignee_id.isdigit() else None
    cat_id = int(category_id) if category_id and category_id.isdigit() else None
    if cat_id:
        query = query.filter(models.Task.category_id == cat_id)

    tasks = query.all()

    # Organized for Kanban
    tasks_todo = [t for t in tasks if t.status == 'Todo']
    tasks_inprogress = [t for t in tasks if t.status == 'In Progress']
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
            "url": f"javascript:openEditModal('{t.id}', '{t.title}', '{t.description or ''}', '{t.status}', '{t.department or ''}', {[u.id for u in t.assignees]}, '{t.start_date or ''}', '{t.due_date or ''}', '{t.project_id or 0}', '{t.category_id or 0}', {[f.filename for f in t.files]}, {[f.filepath for f in t.files]})"
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

    users = db.query(models.User).all()
    categories = db.query(models.Category).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "tasks_todo": tasks_todo,
        "tasks_inprogress": tasks_inprogress,
        "tasks_done": tasks_done,
        "calendar_events": calendar_events, # Pass to template
        "users": users,
        "categories": categories,
        "projects": db.query(models.Project).all(), # Pass projects for modal
        "selected_assignee": a_id,
        "selected_category": cat_id,
        "selected_department": department, # Pass back to UI
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
                assignee_ids: List[int] = Form([]),
                category_id: int = Form(None),
                department: str = Form(None),
                db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    date_obj = None
    start_date_obj = None
    if due_date:
        date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()

    if project_id == 0: project_id = None
    if project_id == 0: project_id = None
    if category_id == 0: category_id = None

    new_task = models.Task(
        title=title,
        description=description,
        status=status,
        start_date=start_date_obj,
        due_date=date_obj,
        project_id=project_id,
        category_id=category_id,
        department=department,
        creator_id=current_user.id if current_user else None
    )
    db.add(new_task)
    db.commit()
    
    # Handle multiple assignees
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        new_task.assignees = users
        # Legacy support
        if users:
            new_task.assignee_id = users[0].id
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
    if current_user.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    users = db.query(models.User).all()
    categories = db.query(models.Category).all()
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "user": current_user,
        "users": users, 
        "categories": categories
    })

@app.post("/admin/users", response_class=RedirectResponse)
@app.post("/admin/users", response_class=RedirectResponse)
def create_user(username: str = Form(...), 
                department: str = Form(None),
                email: str = Form(None),
                phone: str = Form(None),
                position: str = Form(None),
                password: str = Form(...), # Require password for new users
                db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    if current_user.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    
    new_user = models.User(
        username=username,
        department=department,
        email=email,
        phone=phone,
        position=position,
        password_hash=get_password_hash(password)
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
                password: str = Form(None), # Optional for updates
                db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    if current_user.role != "admin":
        return RedirectResponse(url="/", status_code=303)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.username = username
        user.department = department
        user.email = email
        user.phone = phone
        user.position = position
        
        if password and password.strip():
            user.password_hash = get_password_hash(password)
            
        db.commit()
        
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/users/{user_id}/delete", response_class=RedirectResponse)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    if current_user.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if user_to_delete:
        # Prevent deleting the admin user itself if it's the one logged in (optional but good practice)
        if user_to_delete.id == current_user.id:
             # Ideally show error, but for now just redirect
             return RedirectResponse(url="/admin", status_code=303)

        # 1. Unlink from Created Projects/Tasks (Set creator_id = NULL)
        db.query(models.Project).filter(models.Project.creator_id == user_id).update({"creator_id": None})
        db.query(models.Task).filter(models.Task.creator_id == user_id).update({"creator_id": None})
        
        # 2. Unlink from Assigned Tasks (Legacy assignee_id = NULL)
        db.query(models.Task).filter(models.Task.assignee_id == user_id).update({"assignee_id": None})
        
        # 3. Remove from M2M Associations
        # We need to manually delete from association tables or let SQLAlchemy cascade if configured. 
        # Since we didn't set cascade="all, delete", we should manually clear.
        # However, deleting the User object might fail if foreign keys enforce constraint. 
        # Let's remove them from the relationships.
        
        # Determine strictness. SQLite by default might not enforce FK unless enabled.
        # But cleanest is to clear associations. 
        # In SQLAlchemy ORM, removing the user object usually requires removing it from collections.
        
        # But easier: Execute DELETE on association tables
        db.execute(models.project_assignees.delete().where(models.project_assignees.c.user_id == user_id))
        db.execute(models.task_assignees.delete().where(models.task_assignees.c.user_id == user_id))
        
        # 4. Delete the User
        db.delete(user_to_delete)
        db.commit()
        
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/categories", response_class=RedirectResponse)
def create_category(name: str = Form(...), color: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    if current_user.role != "admin":
        return RedirectResponse(url="/", status_code=303)
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

@app.post("/projects", response_class=RedirectResponse)
def create_project(name: str = Form(...), description: str = Form(None), 
                   start_date: str = Form(None), end_date: str = Form(None), 
                   status: str = Form(...),
                   department: str = Form(None),
                   assignee_ids: List[int] = Form([]),
                   db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    # Handle YYYY-MM input from type="month"
    s_date = datetime.strptime(start_date, "%Y-%m").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m").date() if end_date else None
    
    new_project = models.Project(
        name=name, 
        description=description, 
        start_date=s_date, 
        end_date=e_date, 
        status=status, 
        department=department,
        creator_id=current_user.id if current_user else None
    )
    db.add(new_project)
    db.commit()
    
    # Handle assignees
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        new_project.assignees = users
        db.commit()
    return RedirectResponse(url="/projects", status_code=303)


@app.post("/projects/{project_id}/update", response_class=RedirectResponse)
def update_project(project_id: int,
                   name: str = Form(...), description: str = Form(None), 
                   start_date: str = Form(None), end_date: str = Form(None), 
                   status: str = Form(...),
                   department: str = Form(None),
                   assignee_ids: List[int] = Form([]),
                   db: Session = Depends(get_db)):
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
         return RedirectResponse(url="/projects", status_code=303)

    # Handle YYYY-MM input from type="month"
    s_date = datetime.strptime(start_date, "%Y-%m").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m").date() if end_date else None
    
    project.name = name
    project.description = description
    project.start_date = s_date
    project.end_date = e_date
    project.status = status
    project.department = department
    
    # Update Assignees
    # We replace the list entirely
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        project.assignees = users
    else:
        project.assignees = []
    
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
                assignee_ids: List[int] = Form([]),
                due_date: str = Form(None),
                project_id: int = Form(0),
                category_id: int = Form(0),
                department: str = Form(None),
                db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    new_task = models.Task(
        title=title,
        description=description,
        status=status,
        due_date=datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None,
        project_id=project_id if project_id != 0 else None,
        category_id=category_id if category_id != 0 else None,
        department=department,
        creator_id=current_user.id if current_user else None
    )
    db.add(new_task)
    db.commit()
    
    if assignee_ids:
        users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
        new_task.assignees = users
        if users: new_task.assignee_id = users[0].id
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
                        category_id: int = Form(0),
                        department: str = Form(None),
                        db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.title = title
        task.description = description
        task.status = status
        
        # Update assignees
        if assignee_ids:
            users = db.query(models.User).filter(models.User.id.in_(assignee_ids)).all()
            task.assignees = users
            if users: task.assignee_id = users[0].id
        else:
            task.assignees = []
            task.assignee_id = None

        task.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        task.project_id = project_id if project_id != 0 else None
        task.category_id = category_id if category_id != 0 else None
        task.department = department
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
        filepath=f"/uploads/{filename}",
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
def create_meeting_minute(request: Request, 
                          topic: str = Form(...), 
                          date_str: str = Form(...),
                          time: str = Form(None),
                          location: str = Form(None),
                          attendees: str = Form(None),
                          content: str = Form(...),
                          files: List[UploadFile] = File(None),
                          db: Session = Depends(get_db),
                          current_user: models.User = Depends(get_current_user)):
    if not current_user: return RedirectResponse(url="/login", status_code=303)
    
    # date_str from input type="date" is YYYY-MM-DD
    m_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
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

    # Handle file uploads
    if files:
        upload_dir = "uploads/meeting_minutes"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        for file in files:
            if file.filename: # check if filename is not empty
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{timestamp}_{file.filename}"
                filepath = os.path.join(upload_dir, filename)
                
                with open(filepath, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                new_file = models.MeetingMinuteFile(
                    filename=file.filename,
                    filepath=f"/uploads/meeting_minutes/{filename}",
                    meeting_minute_id=new_minute.id
                )
                db.add(new_file)
        db.commit()
    
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
