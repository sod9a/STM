import sys
import os
sys.path.append(os.getcwd())
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('tickets')]
    print(f"COLUMNS: {columns}")
    
    if 'assigned_to_id' not in columns:
        print("MISSING assigned_to_id. Attempting to add...")
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN assigned_to_id INTEGER REFERENCES users(id)"))
                conn.commit()
            print("Successfully added assigned_to_id column.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("assigned_to_id column exists.")
        
    if not inspector.has_table('comments'):
        print("MISSING comments table. Creating...")
        db.create_all()
        print("Tables created.")
    else:
        print("comments table exists.")

    if not inspector.has_table('notifications'):
        print("MISSING notifications table. Creating...")
        db.create_all()
        print("Notifications table created.")
    else:
        print("notifications table exists.")
