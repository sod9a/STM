import os
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    inspector = inspect(engine)

    columns = [c['name'] for c in inspector.get_columns('tickets')]
    print("COLUMNS:", columns)

    if 'assigned_to_id' not in columns:
        print("Adding assigned_to_id...")
        conn.execute(text("""
            ALTER TABLE tickets
            ADD COLUMN assigned_to_id INTEGER
        """))
        conn.commit()
        print("DONE")

    if not inspector.has_table('comments'):
        print("Creating comments table...")
        conn.execute(text("CREATE TABLE comments (id SERIAL PRIMARY KEY)"))
        conn.commit()

    if not inspector.has_table('notifications'):
        print("Creating notifications table...")
        conn.execute(text("CREATE TABLE notifications (id SERIAL PRIMARY KEY)"))
        conn.commit()