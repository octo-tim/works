import datetime

from database import engine, SessionLocal
import models
from passlib.context import CryptContext


# Drop existing tables
models.Base.metadata.drop_all(bind=engine)

# Create tables
models.Base.metadata.create_all(bind=engine)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    """비밀번호 해시 생성"""
    return pwd_context.hash(password)


db = SessionLocal()

# Create Admin User
admin_user = models.User(
    username="윤경식",
    password_hash=get_password_hash("k0349001!"),
    department="System",
    role="admin"
)
db.add(admin_user)

# Create System Test User
sys_user = models.User(
    username="TestUser",
    password_hash=get_password_hash("password123"),
    department="System",
    role="user"
)
db.add(sys_user)

# Create Distribution Test User
dist_user = models.User(
    username="DistUser",
    password_hash=get_password_hash("password123"),
    department="Distribution",
    role="user"
)
db.add(dist_user)

db.commit()

# Create Projects
project1 = models.Project(
    name="Mobile App Redesign",
    description="Redesigning the main mobile application",
    status="In Progress",
    start_date=datetime.date(2025, 1, 1),
)
db.add(project1)

db.commit()
db.close()

print("Database initialized with admin and test users.")
