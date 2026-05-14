from app import app, db, User, Ticket, Comment, Notification, Peminjaman, SoftwareUser, TempahanBilik

def remove_users():
    with app.app_context():
        usernames_to_remove = ['USER', 'Ak', 'arief', 'razifalhaj', 'testpengguna']
        
        for username in usernames_to_remove:
            user = User.query.filter_by(username=username).first()
            if user:
                user_id = user.id
                print(f"Deleting user {username} (ID: {user_id}) and related records...")
                
                # Delete related notifications
                Notification.query.filter_by(user_id=user_id).delete()
                
                # Delete related comments
                Comment.query.filter_by(user_id=user_id).delete()
                
                # Delete related software assignments
                SoftwareUser.query.filter_by(user_id=user_id).delete()
                SoftwareUser.query.filter_by(assigned_by_id=user_id).delete()
                
                # Delete related room bookings
                TempahanBilik.query.filter_by(user_id=user_id).delete()
                # For approved_by_id, we set it to null instead of deleting the whole booking?
                # Actually, if the admin who approved it is deleted, we can set approved_by_id to null
                TempahanBilik.query.filter_by(approved_by_id=user_id).update({TempahanBilik.approved_by_id: None})
                
                # Delete related asset borrowing
                Peminjaman.query.filter_by(user_id=user_id).delete()
                Peminjaman.query.filter_by(approved_by_id=user_id).update({Peminjaman.approved_by_id: None})
                
                # Handle Tickets
                # 1. Tickets authored by this user
                authored_tickets = Ticket.query.filter_by(user_id=user_id).all()
                for ticket in authored_tickets:
                    # Deleting comments on this ticket first (should be handled by cascade but let's be safe)
                    Comment.query.filter_by(ticket_id=ticket.id).delete()
                    db.session.delete(ticket)
                
                # 2. Tickets assigned to this user
                Ticket.query.filter_by(assigned_to_id=user_id).update({Ticket.assigned_to_id: None})
                Ticket.query.filter_by(proposed_assignee_id=user_id).update({Ticket.proposed_assignee_id: None})
                
                # Finally delete the user
                db.session.delete(user)
                print(f"User {username} and all related records deleted.")
            else:
                print(f"User {username} not found.")
        
        db.session.commit()
        print("Done!")

if __name__ == "__main__":
    remove_users()
