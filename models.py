from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

from sqlalchemy import Table

# Association tables
project_assignees = Table('project_assignees', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

task_assignees = Table('task_assignees', Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    department = Column(String) # "System", "Distribution", "Management" (Admin)
    role = Column(String, default="user") # "admin", "user"
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    position = Column(String, nullable=True) # e.g. "Manager", "Designer"

    tasks_assigned = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    








class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String, default="Scheduled") # Scheduled, In Progress, Completed
    department = Column(String, nullable=True) # "System", "Distribution"
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    creator = relationship("User", foreign_keys=[creator_id])
    assignees = relationship("User", secondary=project_assignees, backref="projects_assigned")
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
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Kept for backward compat, but we prefer 'assignees'
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)


    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id]) # Legacy single assignee
    creator = relationship("User", foreign_keys=[creator_id])
    assignees = relationship("User", secondary=task_assignees, backref="tasks_multi_assigned")
    files = relationship("TaskFile", back_populates="task")
    progresses = relationship("TaskProgress", back_populates="task", order_by="desc(TaskProgress.date)")


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




class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_all_day = Column(Boolean, default=False)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    department = Column(String, nullable=True) # For easier department filtering

    user = relationship("User", backref="events")


class TodaysCheck(Base):
    __tablename__ = "todays_checks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    # Using 'date' specifically for easy filtering by day, 
    # though created_at covers it, having a dedicated date column can be simpler for queries if needed
    # but the plan stuck to created_at is fine. Let's add date for robustness since plan mentioned it originally
    # Plan said: Fields: id, sender_id, receiver_id, content, created_at, date.
    # Code snippet in plan didn't have date, but text did. I'll add it to be safe/cleaner.
    date = Column(Date, default=datetime.date.today)
    
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class TaskProgress(Base):
    __tablename__ = "task_progress"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    writer_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    date = Column(Date, default=datetime.date.today) # User specified date for the progress

    task = relationship("Task", back_populates="progresses")
    writer = relationship("User")


class WorkTemplate(Base):
    __tablename__ = "work_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    description = Column(String)
    content_json = Column(Text) # Stores phases/tasks as JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.datetime.utcnow)
    
    creator_id = Column(Integer, ForeignKey("users.id"))
    editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    creator = relationship("User", foreign_keys=[creator_id])
    editor = relationship("User", foreign_keys=[editor_id])


class WorkReport(Base):
    __tablename__ = "work_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String) # DAILY, WEEKLY, MONTHLY
    start_date = Column(Date)
    end_date = Column(Date)
    summary = Column(Text, nullable=True)
    evaluation = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)

    user = relationship("User", backref="work_reports")
