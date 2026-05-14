from app import app, db, User

def list_users():
    with app.app_context():
        users = User.query.filter(User.username.in_(['Ak', 'arief'])).all()
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Full Name: {u.full_name}, Dept: {u.department}")

if __name__ == "__main__":
    list_users()
