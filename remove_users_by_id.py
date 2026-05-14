from app import app, db, User, Notification, Comment, SoftwareUser, TempahanBilik, Peminjaman, Ticket

def remove_users_by_id():
    with app.app_context():
        user_ids = [482, 483]
        
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                print(f"Deleting user {user.username} (ID: {user_id})...")
                
                # Delete related records
                Notification.query.filter_by(user_id=user_id).delete()
                Comment.query.filter_by(user_id=user_id).delete()
                SoftwareUser.query.filter_by(user_id=user_id).delete()
                SoftwareUser.query.filter_by(assigned_by_id=user_id).delete()
                TempahanBilik.query.filter_by(user_id=user_id).delete()
                TempahanBilik.query.filter_by(approved_by_id=user_id).update({TempahanBilik.approved_by_id: None})
                Peminjaman.query.filter_by(user_id=user_id).delete()
                Peminjaman.query.filter_by(approved_by_id=user_id).update({Peminjaman.approved_by_id: None})
                
                # Tickets authored
                authored_tickets = Ticket.query.filter_by(user_id=user_id).all()
                for ticket in authored_tickets:
                    Comment.query.filter_by(ticket_id=ticket.id).delete()
                    db.session.delete(ticket)
                
                # Tickets assigned
                Ticket.query.filter_by(assigned_to_id=user_id).update({Ticket.assigned_to_id: None})
                Ticket.query.filter_by(proposed_assignee_id=user_id).update({Ticket.proposed_assignee_id: None})
                
                db.session.delete(user)
                print(f"User {user.username} (ID: {user_id}) deleted.")
            else:
                print(f"User ID {user_id} not found.")
        
        db.session.commit()
        print("Done!")

if __name__ == "__main__":
    remove_users_by_id()
