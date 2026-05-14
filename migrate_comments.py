from flask import Flask
from models import db
from config import Config
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def migrate():
    with app.app_context():
        print("Connecting to PostgreSQL database...")
        try:
            db.session.execute(text("ALTER TABLE comments ADD COLUMN attachment_filename VARCHAR(255)"))
            db.session.commit()
            print("Column 'attachment_filename' added successfully!")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("Column 'attachment_filename' already exists.")
            else:
                print(f"An error occurred: {e}")
                db.session.rollback()

if __name__ == '__main__':
    migrate()
