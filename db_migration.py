from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Migrating users table (SQLite Mode)...")
        columns = ["email", "phone", "position"]
        for col in columns:
            try:
                # SQLite syntax: simple ADD COLUMN
                sql = text(f"ALTER TABLE users ADD COLUMN {col} VARCHAR")
                conn.execute(sql)
                print(f"Added column: {col}")
            except Exception as e:
                # Ignore error if column likely exists
                print(f"Skipping {col} (likely already exists or error): {e}")
        conn.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
