import sys
import os
sys.path.append(os.getcwd())
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('tickets')]
    
    if 'proposed_assignee_id' not in columns:
        print("MISSING proposed_assignee_id. Attempting to add...")
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN proposed_assignee_id INTEGER REFERENCES users(id)"))
                conn.commit()
            print("Successfully added proposed_assignee_id column.")
        except Exception as e:
            print(f"Error adding proposed_assignee_id column: {e}")
    else:
        print("proposed_assignee_id column exists.")
