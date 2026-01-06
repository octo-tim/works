import os
import sys
from sqlalchemy import create_engine, text

def fix_schema():
    # Get database URL from argument or environment
    db_url = os.getenv("DATABASE_URL")
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    
    if not db_url:
        print("Error: Please provide the DATABASE_URL as an environment variable or command line argument.")
        print("Usage: DATABASE_URL='postgresql://...' python3 fix_production_schema.py")
        return

    # Fix postgres:// compatible with sqlalchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to database...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("Successfully connected. checking schema...")
            
            columns = [
                ("email", "VARCHAR"), 
                ("phone", "VARCHAR"), 
                ("position", "VARCHAR")
            ]

            # 2. Fix work_templates table
            work_template_columns = [
                ("updated_at", "TIMESTAMP"),
                ("editor_id", "INTEGER")
            ]
            
            # Helper to add columns
            def add_columns(table_name, cols):
                for col_name, col_type in cols:
                    try:
                        print(f"Attempting to add column '{col_name}' to '{table_name}'...")
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        print(f" -> Added column: {col_name}")
                    except Exception as e:
                        conn.rollback() 
                        if "already exists" in str(e) or "duplicate column" in str(e):
                             print(f" -> Column '{col_name}' already exists in '{table_name}'. Skipping.")
                        else:
                            print(f" -> Error adding {col_name} to {table_name}: {e}")

            # Run helpers
            add_columns("users", columns)
            add_columns("work_templates", work_template_columns)
            
            # Skip the old loop logic below
            columns = []
            
            for col_name, col_type in columns:
                try:
                    # PostgreSQL specific check and add
                    # Using exception handling for simplicity as IF NOT EXISTS slightly varies by version or requires procedure
                    print(f"Attempting to add column '{col_name}'...")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    print(f" -> Added column: {col_name}")
                except Exception as e:
                    # Check if error is "Duplicate column"
                    conn.rollback() # Rollback the failed transaction so we can continue
                    if "already exists" in str(e) or "duplicate column" in str(e):
                         print(f" -> Column '{col_name}' already exists. Skipping.")
                    else:
                        print(f" -> Error adding {col_name}: {e}")
            
            conn.commit()
            print("Schema update finished.")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    fix_schema()
