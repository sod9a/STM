import sys
import os
sys.path.append(os.getcwd())
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('tickets')]
    
    if 'priority' not in columns:
        print("MISSING priority. Attempting to add...")
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN priority VARCHAR(20) DEFAULT 'Rendah'"))
                conn.commit()
            print("Successfully added priority column.")
        except Exception as e:
            print(f"Error adding priority column: {e}")
    else:
        print("priority column exists.")
