from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE peminjaman ADD COLUMN reject_reason TEXT'))
        db.session.commit()
        print("Column reject_reason added successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
