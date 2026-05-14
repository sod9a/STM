from app import app, db
from sqlalchemy import text

def add_pending_profile_column():
    with app.app_context():
        print("Checking for 'pending_profile_picture' column in 'users' table...")
        try:
            # Check if column exists
            db.session.execute(text("SELECT pending_profile_picture FROM users LIMIT 1"))
            print("Column already exists.")
        except Exception:
            db.session.rollback()
            print("Column missing. Adding 'pending_profile_picture' to 'users' table...")
            try:
                db.session.execute(text("ALTER TABLE users ADD COLUMN pending_profile_picture VARCHAR(255)"))
                db.session.commit()
                print("Column added successfully.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_pending_profile_column()
