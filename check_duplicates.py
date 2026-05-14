from app import app, db, User
from sqlalchemy import func

def check_duplicates():
    with app.app_context():
        print("Checking for duplicate users...")
        
        # 1. Duplicate Usernames (Case-insensitive)
        duplicate_usernames = db.session.query(
            func.lower(User.username), 
            func.count(User.id)
        ).group_by(func.lower(User.username)).having(func.count(User.id) > 1).all()
        
        if duplicate_usernames:
            print("\n[!] Duplicate Usernames found (case-insensitive):")
            for username, count in duplicate_usernames:
                users = User.query.filter(User.username.ilike(username)).all()
                print(f" - '{username}' (Found {count} times):")
                for u in users:
                    print(f"    ID: {u.id}, Actual Username: {u.username}, Email: {u.email_address}")
        else:
            print("\n[v] No duplicate usernames found.")

        # 2. Duplicate Emails
        duplicate_emails = db.session.query(
            User.email_address, 
            func.count(User.id)
        ).filter(User.email_address != None, User.email_address != '').group_by(User.email_address).having(func.count(User.id) > 1).all()
        
        if duplicate_emails:
            print("\n[!] Duplicate Email Addresses found:")
            for email, count in duplicate_emails:
                users = User.query.filter_by(email_address=email).all()
                print(f" - '{email}' (Found {count} times):")
                for u in users:
                    print(f"    ID: {u.id}, Username: {u.username}, Full Name: {u.full_name}")
        else:
            print("\n[v] No duplicate email addresses found.")

        # 3. Duplicate Full Names
        duplicate_names = db.session.query(
            User.full_name, 
            func.count(User.id)
        ).filter(User.full_name != None, User.full_name != '').group_by(User.full_name).having(func.count(User.id) > 1).all()
        
        if duplicate_names:
            print("\n[!] Duplicate Full Names found:")
            for name, count in duplicate_names:
                users = User.query.filter_by(full_name=name).all()
                print(f" - '{name}' (Found {count} times):")
                for u in users:
                    print(f"    ID: {u.id}, Username: {u.username}")
        else:
            print("\n[v] No duplicate full names found.")

if __name__ == "__main__":
    check_duplicates()
