from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    department = Column(String) # "System", "Distribution", "Management" (Admin)
    role = Column(String, default="user") # "admin", "user"

    tasks_assigned = relationship("Task", back_populates="assignee")
    
    # Chat relationships
    messages_sent = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender")
    messages_received = relationship("ChatMessage", foreign_keys="ChatMessage.receiver_id", back_populates="receiver")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    contact_info = Column(String, nullable=True)

    projects = relationship("Project", back_populates="client")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    color = Column(String, default="#000000")

    tasks = relationship("Task", back_populates="category")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String, default="Scheduled") # Scheduled, In Progress, Completed
    department = Column(String, nullable=True) # "System", "Distribution"
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    client = relationship("Client", back_populates="projects")
    tasks = relationship("Task", back_populates="project")
    files = relationship("ProjectFile", back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default="Todo") # Todo, In Progress, Done
    department = Column(String, nullable=True) # "System", "Distribution"
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks_assigned")
    category = relationship("Category", back_populates="tasks")
    files = relationship("TaskFile", back_populates="task")


class TaskFile(Base):
    __tablename__ = "task_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    task_id = Column(Integer, ForeignKey("tasks.id"))

    task = relationship("Task", back_populates="files")


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    project_id = Column(Integer, ForeignKey("projects.id"))

    project = relationship("Project", back_populates="files")


class AnnualGoal(Base):
    __tablename__ = "annual_goals"
    year = Column(Integer, primary_key=True)
    content = Column(Text)

class MonthlyObjective(Base):
    __tablename__ = "monthly_objectives"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer)
    month = Column(Integer)
    division = Column(String) # "System" or "Distribution"
    content = Column(String)

class MonthlyPerformance(Base):
    __tablename__ = "monthly_performances"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer)
    month = Column(Integer)
    division = Column(String) # "System" or "Distribution"
    goal_value = Column(String, default="")
    actual_value = Column(String, default="")

class KeySchedule(Base):
    __tablename__ = "key_schedules"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date) # Specific date for the schedule
    division = Column(String) # "System" or "Distribution"
    content = Column(String) # Single line content usually, but String is fine






class MeetingMinutes(Base):
    __tablename__ = "meeting_minutes"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=datetime.date.today)
    time = Column(String, nullable=True) # New field
    location = Column(String, nullable=True) # New field
    topic = Column(String, index=True)
    attendees = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    writer_id = Column(Integer, ForeignKey("users.id"))
    writer = relationship("User")
    files = relationship("MeetingMinuteFile", back_populates="meeting_minute")


class MeetingMinuteFile(Base):
    __tablename__ = "meeting_minute_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    meeting_minute_id = Column(Integer, ForeignKey("meeting_minutes.id"))

    meeting_minute = relationship("MeetingMinutes", back_populates="files")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")
