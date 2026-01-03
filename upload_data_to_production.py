import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
import database 

# Local DB (Source)
local_db = database.SessionLocal()

def upload_data():
    # Get Remote DB URL (Target)
    remote_url = os.getenv("DATABASE_URL")
    if len(sys.argv) > 1:
        remote_url = sys.argv[1]
    
    if not remote_url:
        print("Error: Please provide the DATABASE_URL (Target) as an environment variable or argument.")
        return

    if remote_url.startswith("postgres://"):
        remote_url = remote_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to remote database...")
    remote_engine = create_engine(remote_url)
    RemoteSession = sessionmaker(bind=remote_engine)
    remote_db = RemoteSession()

    print("Starting data upload...")

    # 1. Users
    users = local_db.query(models.User).all()
    print(f"Found {len(users)} users locally.")
    for local_user in users:
        # Check if user exists remotely (by username)
        remote_user = remote_db.query(models.User).filter_by(username=local_user.username).first()
        if not remote_user:
            print(f"Creating user: {local_user.username}")
            new_user = models.User(
                username=local_user.username,
                password_hash=local_user.password_hash,
                department=local_user.department,
                role=local_user.role,
                email=local_user.email,
                phone=local_user.phone,
                position=local_user.position
            )
            remote_db.add(new_user)
        else:
            print(f"Updating user: {local_user.username}")
            remote_user.email = local_user.email
            remote_user.phone = local_user.phone
            remote_user.position = local_user.position
            # Don't overwrite password/role unless needed
    remote_db.commit()

    # 2. Re-fetch remote users to map IDs
    remote_users_map = {u.username: u.id for u in remote_db.query(models.User).all()}

    # 3. Projects
    projects = local_db.query(models.Project).all()
    print(f"Found {len(projects)} projects locally.")
    for p in projects:
        # Find creator remote ID
        creator = local_db.query(models.User).get(p.creator_id) if p.creator_id else None
        remote_creator_id = remote_users_map.get(creator.username) if creator else None

        # Check existing project by name (simple dedupe)
        remote_project = remote_db.query(models.Project).filter_by(name=p.name).first()
        if not remote_project:
            print(f"Creating project: {p.name}")
            new_p = models.Project(
                name=p.name,
                description=p.description,
                status=p.status,
                department=p.department,
                start_date=p.start_date,
                end_date=p.end_date,
                creator_id=remote_creator_id,
                # Copy file metadata loosely
                filenames=p.filenames,
                filepaths=p.filepaths 
            )
            remote_db.add(new_p)
            remote_db.flush() # get ID
            remote_project = new_p
        
        # Sync Assignees
        # Clear existing? Or merge? Let's merge/set
        remote_project.assignees = []
        for local_u in p.assignees:
            rid = remote_users_map.get(local_u.username)
            if rid:
                ru = remote_db.query(models.User).get(rid)
                remote_project.assignees.append(ru)

    remote_db.commit()
    print("Data upload complete.")

if __name__ == "__main__":
    upload_data()
