from app import app
from models import db, User
import openpyxl
import os

def import_users(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    try:
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        
        success_count = 0
        error_count = 0
        duplicate_count = 0

        with app.app_context():
            # Iterate through rows, skipping header if necessary
            # The user said Column A is username, Column B is password
            for row_idx, row in enumerate(sheet.iter_rows(min_row=1, values_only=True), start=1):
                username   = str(row[0]).strip() if row[0] is not None else None
                password   = str(row[1]).strip() if row[1] is not None else None
                department = str(row[2]).strip() if row[2] is not None else None
                full_name  = str(row[3]).strip() if len(row) > 3 and row[3] is not None else None
                working_grade = str(row[4]).strip() if len(row) > 4 and row[4] is not None else None
                phone_number  = str(row[5]).strip() if len(row) > 5 and row[5] is not None else None
                work_position = str(row[7]).strip() if len(row) > 7 and row[7] is not None else None

                # Sanitize 'None' strings
                if full_name == 'None':      full_name = None
                if working_grade == 'None':  working_grade = None
                if phone_number == 'None':   phone_number = None
                if work_position == 'None':  work_position = None

                if not username or not password or username == 'None' or password == 'None':
                    print(f"Row {row_idx}: Skipping empty or invalid data (Username: {username})")
                    continue

                # Check for header row
                if username.lower() in ('username', 'nama pengguna'):
                    print(f"Row {row_idx}: Skipping header row")
                    continue

                # Update or create user
                user = User.query.filter(User.username.ilike(username)).first()
                if user:
                    user.password      = password
                    user.department    = department
                    user.full_name     = full_name
                    user.working_grade = working_grade
                    user.phone_number  = phone_number
                    user.work_position = work_position
                    action = "Updated"
                else:
                    user = User(
                        username=username, password=password, role='user',
                        department=department, full_name=full_name,
                        working_grade=working_grade, phone_number=phone_number,
                        work_position=work_position
                    )
                    db.session.add(user)
                    action = "Imported"

                try:
                    db.session.commit()
                    success_count += 1
                    print(f"Row {row_idx}: {action} '{username}' | Nama: {full_name} | Gred: {working_grade} | Tel: {phone_number}")
                except Exception as e:
                    db.session.rollback()
                    print(f"Row {row_idx}: Error processing '{username}': {str(e)}")
                    error_count += 1

        print("\n--- Import Summary ---")
        print(f"Success: {success_count}")
        print(f"Duplicates skipped: {duplicate_count}")
        print(f"Errors: {error_count}")
        print("----------------------")

    except Exception as e:
        print(f"Critical Error: {str(e)}")

if __name__ == "__main__":
    EXCEL_FILE = "USER LIST.xlsx"
    import_users(EXCEL_FILE)
