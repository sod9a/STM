from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # 'admin' or 'user'
    
    # Profile fields
    full_name = db.Column(db.String(200), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    work_position = db.Column(db.String(100), nullable=True)
    working_grade = db.Column(db.String(50), nullable=True)
    email_address = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    pending_profile_picture = db.Column(db.String(255), nullable=True)

    
    # Relationship
    tickets = db.relationship('Ticket', backref='author', lazy=True, foreign_keys='Ticket.user_id')

    def __repr__(self):
        return f'<User {self.username}>'

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Lain-lain')
    priority = db.Column(db.String(20), default='Rendah')
    status = db.Column(db.String(50), default="Open")
    attachment = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Existing tickets are NULL
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    proposed_assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    comments = db.relationship('Comment', backref='ticket', lazy=True, cascade="all, delete-orphan")
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='tickets_assigned', lazy=True)
    proposed_assignee = db.relationship('User', foreign_keys=[proposed_assignee_id], backref='proposed_tickets', lazy=True)

    def __repr__(self):
        return f'<Ticket {self.id}: {self.title}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    attachment_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = db.relationship('User', backref='comments', lazy=True)

    def __repr__(self):
        return f'<Comment {self.id} on Ticket {self.ticket_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', order_by='Notification.created_at.desc()'))

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

class Peminjaman(db.Model):
    __tablename__ = 'peminjaman'
    
    id = db.Column(db.Integer, primary_key=True)
    aset = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    lokasi = db.Column(db.String(255), nullable=False)
    lokasi_lain = db.Column(db.String(255), nullable=True)
    purpose = db.Column(db.Text, nullable=False)
    borrow_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default="Pending") # Pending, Approved, Rejected, Returned
    reject_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('peminjaman_requests', lazy=True))
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_peminjaman', lazy=True)
    pemulangan_items = db.relationship('PemulanganItem', backref='peminjaman', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Peminjaman {self.id}: {self.aset}>'


class PemulanganItem(db.Model):
    """Tracks individual item returns with specific dates for a Peminjaman."""
    __tablename__ = 'pemulangan_items'

    id = db.Column(db.Integer, primary_key=True)
    peminjaman_id = db.Column(db.Integer, db.ForeignKey('peminjaman.id'), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)   # e.g. "Extension 1"
    returned_at = db.Column(db.DateTime, nullable=False)    # specific return date chosen by admin
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    processed_by = db.relationship('User', foreign_keys=[processed_by_id], backref='processed_pemulangan', lazy=True)

    def __repr__(self):
        return f'<PemulanganItem {self.item_name} @ {self.returned_at}>'

class AsetInventory(db.Model):
    __tablename__ = 'aset_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False) # e.g. Laptop, Projector, Monitor
    name = db.Column(db.String(255), nullable=False, unique=True) # e.g. POOL Laptop A1
    serial_number = db.Column(db.String(255), nullable=True)
    tag_id = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    is_available = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<AsetInventory {self.name} - {"Available" if self.is_available else "Borrowed"}>'

class SoftwareLicense(db.Model):
    __tablename__ = 'software_licenses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon_class = db.Column(db.String(100), default="bi-box")
    bg_color = db.Column(db.String(50), default="rgba(56,145,220,0.1)")
    text_color = db.Column(db.String(50), default="#3891dc")
    total_licenses = db.Column(db.Integer, default=10, nullable=False)
    
    # Relationships
    assigned_users = db.relationship('SoftwareUser', backref='software', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<SoftwareLicense {self.name}>'

class SoftwareUser(db.Model):
    __tablename__ = 'software_users'
    
    id = db.Column(db.Integer, primary_key=True)
    software_id = db.Column(db.Integer, db.ForeignKey('software_licenses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('assigned_software', lazy=True))
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id], backref='software_assigned_by', lazy=True)

    def __repr__(self):
        return f'<SoftwareUser {self.software_id} -> {self.user_id}>'

class TempahanBilik(db.Model):
    __tablename__ = 'tempahan_bilik'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default="Pending") # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('tempahan_bilik', lazy=True))
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_tempahan', lazy=True)

    def __repr__(self):
        return f'<TempahanBilik {self.id} -> {self.status}>'

class Broadcast(db.Model):
    __tablename__ = 'broadcasts'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    creator = db.relationship('User', backref='broadcasts', lazy=True)

    def __repr__(self):
        return f'<Broadcast {self.id} - {"Active" if self.is_active else "Inactive"}>'
