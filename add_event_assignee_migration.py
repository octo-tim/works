import sqlite3

def migrate():
    conn = sqlite3.connect('sql_app.db')
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(events)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'assignee_id' not in columns:
            print("Adding assignee_id column to events table...")
            cursor.execute("ALTER TABLE events ADD COLUMN assignee_id INTEGER REFERENCES users(id)")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column assignee_id already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
