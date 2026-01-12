import os
import sys
import traceback
from sqlalchemy import create_engine, text


def fix_schema(db_url=None):
    """데이터베이스 스키마 마이그레이션 수행"""
    logs = []

    def log(msg):
        print(msg)
        logs.append(str(msg))

    # Get database URL from argument or environment
    if not db_url:
        db_url = os.getenv("DATABASE_URL")

    # Only check sys.argv if we are running as main script (not imported)
    if __name__ == "__main__" and len(sys.argv) > 1:
        db_url = sys.argv[1]

    if not db_url:
        log("Error: Please provide the DATABASE_URL as an environment variable or command line argument.")
        log("Usage: DATABASE_URL='postgresql://...' python3 fix_production_schema.py")
        return logs

    # Fix postgres:// compatible with sqlalchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    log("Connecting to database...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            log("Successfully connected. checking schema...")

            columns = [
                ("email", "VARCHAR"),
                ("phone", "VARCHAR"),
                ("position", "VARCHAR")
            ]

            # Fix work_templates table
            work_template_columns = [
                ("created_at", "TIMESTAMP"),
                ("updated_at", "TIMESTAMP"),
                ("creator_id", "INTEGER"),
                ("editor_id", "INTEGER")
            ]

            # Helper to add columns
            def add_columns(table_name, cols):
                for col_name, col_type in cols:
                    try:
                        log(f"Attempting to add column '{col_name}' to '{table_name}'...")
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        log(f" -> Added column: {col_name}")
                    except Exception as e:
                        conn.rollback()
                        if "already exists" in str(e) or "duplicate column" in str(e):
                            log(f" -> Column '{col_name}' already exists in '{table_name}'. Skipping.")
                        else:
                            log(f" -> Error adding {col_name} to {table_name}: {e}")

            # Run helpers
            add_columns("users", columns)
            add_columns("work_templates", work_template_columns)

            conn.commit()
            log("Schema update finished.")

    except Exception as e:
        log(f"Connection failed: {e}")
        log(traceback.format_exc())

    return logs


if __name__ == "__main__":
    fix_schema()
