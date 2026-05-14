from app import app, db, User

def create_users():
    with app.app_context():
        users_to_add = [
            {'username': 'USER', 'full_name': 'PENGGUNA AM', 'dept': 'BTM', 'role': 'user'},
            {'username': 'Ak', 'full_name': 'AKARIEF', 'dept': 'BTM', 'role': 'user'},
            {'username': 'arief', 'full_name': 'MOHAMAD ARIEF', 'dept': 'BKP', 'role': 'user'},
            {'username': 'razifalhaj', 'full_name': 'RAZIFAL HAJ', 'dept': 'BPA', 'role': 'user'},
            {'username': 'testpengguna', 'full_name': 'TEST PENGGUNA', 'dept': 'BDD', 'role': 'user'}
        ]
        
        for u_data in users_to_add:
            # Check if user exists
            existing = User.query.filter_by(username=u_data['username']).first()
            if not existing:
                new_user = User(
                    username=u_data['username'],
                    password='password123', # Default password
                    full_name=u_data['full_name'],
                    department=u_data['dept'],
                    role=u_data['role'],
                    work_position='KAKITANGAN',
                    working_grade='N19'
                )
                db.session.add(new_user)
                print(f"User {u_data['username']} created.")
            else:
                print(f"User {u_data['username']} already exists.")
        
        db.session.commit()
        print("Done!")

if __name__ == "__main__":
    create_users()
