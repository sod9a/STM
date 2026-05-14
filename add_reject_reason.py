import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'helpdesk.db')
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE peminjaman ADD COLUMN reject_reason TEXT")
        conn.commit()
        print("Successfully added reject_reason column.")
    except sqlite3.OperationalError as e:
        print(f"Error (maybe column already exists?): {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
