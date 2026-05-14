import psycopg2
from config import Config

def reset_db():
    try:
        # Connect to Helpdesk database
        conn = psycopg2.connect(
            dbname="Helpdesk",
            user="postgres",
            password="1234",
            host="127.0.0.1",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Drop existing tables to force recreation with new schema
        cur.execute("DROP TABLE IF EXISTS tickets CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        
        print("Tables dropped successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == "__main__":
    reset_db()
