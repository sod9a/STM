from app import app, db, User

def list_all_problematic_users():
    with app.app_context():
        print("Searching for users with 'Ak' or 'arief' in username (case-insensitive)...")
        users = User.query.filter(
            (User.username.ilike('%Ak%')) | 
            (User.username.ilike('%arief%'))
        ).all()
        
        if users:
            for u in users:
                print(f"ID: {u.id}, Username: {u.username}, Full Name: {u.full_name}, Dept: {u.department}")
        else:
            print("No users found with those keywords.")

        print("\nSearching for users with NO department...")
        no_dept_users = User.query.filter((User.department == None) | (User.department == '')).all()
        for u in no_dept_users:
            print(f"ID: {u.id}, Username: {u.username}, Full Name: {u.full_name}")

if __name__ == "__main__":
    list_all_problematic_users()
