from database import engine, SessionLocal
import models
from passlib.context import CryptContext
import datetime

# Drop existing tables
models.Base.metadata.drop_all(bind=engine)

# Create tables
models.Base.metadata.create_all(bind=engine)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
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

# Create Categories
categories = ["기획", "디자인", "개발", "테스트"]
for name in categories:
    db.add(models.Category(name=name))

# Create Clients
clients = ["ClientA", "ClientB", "ClientC"]
for name in clients:
    db.add(models.Client(name=name, contact_info="Manager Kim"))

db.commit()

# Create Projects
client_a = db.query(models.Client).filter_by(name="ClientA").first()
project1 = models.Project(
    name="Mobile App Redesign",
    description="Redesigning the main mobile application",
    status="In Progress",
    start_date=datetime.date(2025, 1, 1),
    client_id=client_a.id
)
db.add(project1)

db.commit()
db.close()

print("Database initialized with admin and test users.")
