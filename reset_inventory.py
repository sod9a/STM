from app import app, db
from models import AsetInventory

def reset():
    with app.app_context():
        # Drop only AsetInventory table if it exists
        try:
            AsetInventory.__table__.drop(db.engine)
        except Exception as e:
            print(f"Error dropping table: {e}")
            
        db.create_all()
        print("Recreated AsetInventory table.")

if __name__ == '__main__':
    reset()
