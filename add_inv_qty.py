from app import app, db
from sqlalchemy import text

def add_inventory_quantity_column():
    with app.app_context():
        print("Checking for 'quantity' column in 'aset_inventory' table...")
        try:
            # Check if column exists
            db.session.execute(text("SELECT quantity FROM aset_inventory LIMIT 1"))
            print("Column already exists.")
        except Exception:
            db.session.rollback()
            print("Column missing. Adding 'quantity' to 'aset_inventory' table...")
            try:
                db.session.execute(text("ALTER TABLE aset_inventory ADD COLUMN quantity INTEGER DEFAULT 1"))
                db.session.commit()
                print("Column added successfully.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_inventory_quantity_column()
