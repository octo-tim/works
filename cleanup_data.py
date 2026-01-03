from sqlalchemy.orm import Session
from database import SessionLocal
import models

def cleanup_sample_data():
    db = SessionLocal()
    try:
        print("Cleaning up sample data...")
        
        # 1. Delete Tasks
        sample_task_titles = ["Design Mockup", "Frontend Setup", "API Specs", "Client Meeting"]
        db.query(models.Task).filter(models.Task.title.in_(sample_task_titles)).delete(synchronize_session=False)
        print(f"Deleted sample tasks.")

        # 2. Delete Projects
        sample_proj_names = ["Website Redesign", "Mobile App MVP"]
        db.query(models.Project).filter(models.Project.name.in_(sample_proj_names)).delete(synchronize_session=False)
        print(f"Deleted sample projects.")

        # 3. Delete Clients
        sample_clients = ["Samsung Electronics", "Naver"]
        db.query(models.Client).filter(models.Client.name.in_(sample_clients)).delete(synchronize_session=False)
        print(f"Deleted sample clients.")

        # 4. Delete Users (Except Admin and maybe valid users)
        sample_users = ["Kim Manager", "Lee Designer"]
        db.query(models.User).filter(models.User.username.in_(sample_users)).delete(synchronize_session=False)
        print(f"Deleted sample users.")

        # 5. Delete Categories
        sample_cats = ["Development", "Design", "Meeting"]
        db.query(models.Category).filter(models.Category.name.in_(sample_cats)).delete(synchronize_session=False)
        print(f"Deleted sample categories.")

        db.commit()
        print("Sample data cleanup complete.")
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_sample_data()
