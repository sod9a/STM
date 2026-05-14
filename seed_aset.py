from app import app, db
from models import AsetInventory

def seed_inventory():
    with app.app_context():
        db.create_all()
        
        # Clear existing inventory
        AsetInventory.query.delete()
        
        assets_to_add = [
            ('Laptop', 'POOL Laptop A1'),
            ('Laptop', 'POOL Laptop A2'),
            ('Laptop', 'POOL Laptop A3'),
            ('Laptop', 'POOL Laptop C1'),
            ('Laptop', 'POOL Laptop C2'),
            ('Laptop', 'POOL Laptop C3'),
            ('Projector', 'PRJ1'),
            ('Projector', 'PRJ2'),
            ('Projector', 'PRJ3'),
            ('Monitor', 'M1'),
            ('Monitor', 'M2'),
            ('Monitor', 'M3'),
        ]
        
        for cat, name in assets_to_add:
            asset = AsetInventory(category=cat, name=name, is_available=True)
            db.session.add(asset)
            
        db.session.commit()
        print("Inventory seeded successfully!")

if __name__ == '__main__':
    seed_inventory()
