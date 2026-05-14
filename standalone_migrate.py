import psycopg2

def migrate():
    conn_str = 'postgresql://postgres:1234@localhost:5432/Helpdesk'
    print(f"Connecting to database to add column...")
    
    try:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='pending_profile_picture'")
        if cur.fetchone():
            print("Column 'pending_profile_picture' already exists.")
        else:
            print("Adding column 'pending_profile_picture'...")
            cur.execute("ALTER TABLE users ADD COLUMN pending_profile_picture VARCHAR(255)")
            conn.commit()
            print("Column added successfully.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
