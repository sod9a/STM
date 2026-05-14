from app import app, db
from models import TempahanBilik

with app.app_context():
    try:
        TempahanBilik.__table__.create(db.engine)
        print("Table tempahan_bilik created successfully.")
    except Exception as e:
        print(f"Error: {e}")
