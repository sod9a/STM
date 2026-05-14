from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
from functools import wraps
from config import Config
from werkzeug.utils import secure_filename
from models import db, Ticket, User, Comment, Notification, Peminjaman, AsetInventory, SoftwareLicense, SoftwareUser, TempahanBilik, Broadcast
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)
app.config['UPLOAD_FOLDER'] = 'static/img/profiles'
app.config['ATTACHMENT_FOLDER'] = 'static/img/attachments'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4'}

import os
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ATTACHMENT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize extensions
db.init_app(app)

def seed_db():
    """Initial seeding of users."""
    with app.app_context():
        db.create_all()
        # Seed Superadmin
        if not User.query.filter(User.username.ilike('superadmin')).first():
            superadmin = User(username='superadmin', password='123', role='superadmin')
            db.session.add(superadmin)

        try:
            db.session.commit()
            print("Database seeded successfully.")
        except Exception:
            db.session.rollback()
            print("Database already seeded.")

# Run seeding
seed_db()

@app.context_processor
def inject_broadcasts():
    if 'logged_in' in session:
        return {'active_broadcasts': Broadcast.query.filter_by(is_active=True).order_by(Broadcast.created_at.desc()).all()}
    return {'active_broadcasts': []}

# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        if role not in ['admin', 'superadmin']:
            flash('Akses pentadbir diperlukan.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'superadmin':
            flash('Akses pentadbir tertinggi diperlukan.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name     = request.form.get('full_name', '').strip()
        work_position = request.form.get('work_position', '').strip()
        working_grade = request.form.get('working_grade', '').strip()
        email_address = request.form.get('email_address', '').strip()
        phone_number  = request.form.get('phone_number', '').strip()
        username      = request.form.get('username', '').strip()
        password      = request.form.get('password', '')
        confirm_pw    = request.form.get('confirm_password', '')

        # Validate required fields
        if not username or not password or not full_name:
            flash('Nama penuh, nama pengguna dan kata laluan adalah wajib.', 'danger')
            return render_template('register.html')

        if len(password) < 4:
            flash('Kata laluan mestilah sekurang-kurangnya 4 aksara.', 'danger')
            return render_template('register.html')

        if password != confirm_pw:
            flash('Kata laluan tidak sepadan. Sila cuba sekali lagi.', 'danger')
            return render_template('register.html')

        # Check for duplicate usernames (case-insensitive)
        existing = User.query.filter(User.username.ilike(username)).first()
        if existing:
            flash('Nama pengguna ini sudah digunakan. Sila pilih nama pengguna lain.', 'danger')
            return render_template('register.html')

        new_user = User(
            username=username,
            password=password,
            full_name=full_name,
            work_position=work_position,
            working_grade=working_grade,
            email_address=email_address,
            phone_number=phone_number,
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Akaun berjaya didaftarkan! Sila log masuk.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_input = request.form.get('username')
        password_input = request.form.get('password')
        
        # Check against database (case-insensitive)
        user = User.query.filter(User.username.ilike(username_input)).first()
        
        if user and user.password == password_input:
            session['logged_in'] = True
            session['user_id'] = user.id
            session['user'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Nama pengguna atau kata laluan tidak sah.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Email Utility (Disabled per user request)
def send_email(subject, recipient, template, **kwargs):
    # msg = Message(subject, recipients=[recipient])
    # try:
    #     msg.html = render_template(f"emails/{template}.html", **kwargs)
    #     mail.send(msg)
    # except Exception as e:
    #     print(f"Failed to send email: {e}")
    print(f"Email Log: Subject='{subject}', To='{recipient}'")
    return

def create_notification(user_id, message, link=None):
    # Function disabled per user request
    return


@app.route('/')
@login_required
def dashboard():
    from datetime import datetime
    
    role = session.get('role')
    search_query = request.args.get('search', '').strip()
    
    # Base query based on role
    if role in ['admin', 'superadmin']:
        query = Ticket.query.filter(Ticket.status != 'Closed')
    else:
        query = Ticket.query.filter(Ticket.user_id == session.get('user_id'), Ticket.status != 'Closed')
    
    # Apply search filter if query exists
    if search_query:
        search_filter = db.or_(
            Ticket.title.ilike(f'%{search_query}%'),
            Ticket.category.ilike(f'%{search_query}%'),
            Ticket.description.ilike(f'%{search_query}%')
        )
        # Also try to match by ID if numeric
        if search_query.isdigit():
            search_filter = db.or_(search_filter, Ticket.id == int(search_query))
            
        query = query.filter(search_filter)
        
    tickets = query.order_by(Ticket.created_at.desc()).all()
        
    unassigned_tickets = []
    assigned_tickets = []
    if role in ['admin', 'superadmin']:
        unassigned_tickets = [t for t in tickets if not t.assigned_to_id]
        assigned_tickets = [t for t in tickets if t.assigned_to_id == session.get('user_id')]
        
    open_count = sum(1 for t in tickets if t.status == 'Open')
    closed_count = Ticket.query.filter(Ticket.status == 'Closed').count() if role in ['admin', 'superadmin'] else Ticket.query.filter_by(user_id=session.get('user_id'), status='Closed').count()
    
    current_user = User.query.get(session.get('user_id'))
    display_name = current_user.full_name if current_user and current_user.full_name else session.get('user', 'Pengguna')

    # Today's stats
    today = datetime.now().date()

    # --- Panel 1: Permohonan Hari Ini (today's borrowing requests) ---
    if role in ['admin', 'superadmin']:
        permohonan_today = Peminjaman.query.filter(
            db.func.date(Peminjaman.created_at) == today,
            Peminjaman.status != 'Returned',
            Peminjaman.status != 'Approved',
            Peminjaman.status != 'Cancelled'
        ).order_by(Peminjaman.created_at.desc()).all()
    else:
        permohonan_today = Peminjaman.query.filter(
            Peminjaman.user_id == session.get('user_id'),
            db.func.date(Peminjaman.created_at) == today,
            Peminjaman.status != 'Returned',
            Peminjaman.status != 'Approved',
            Peminjaman.status != 'Cancelled'
        ).order_by(Peminjaman.created_at.desc()).all()
    permohonan_hari_ini = len(permohonan_today)

    # --- Panel 2: Tiket Hari Ini (today's tickets) ---
    if role in ['admin', 'superadmin']:
        tiket_today = Ticket.query.filter(
            db.func.date(Ticket.created_at) == today,
            Ticket.status != 'Closed'
        ).order_by(Ticket.created_at.desc()).all()
    else:
        tiket_today = Ticket.query.filter(
            Ticket.user_id == session.get('user_id'),
            db.func.date(Ticket.created_at) == today,
            Ticket.status != 'Closed'
        ).order_by(Ticket.created_at.desc()).all()
    tiket_hari_ini = len(tiket_today)

    # --- Panel 3: Pemulangan (approved/unreturned items with due-date urgency) ---
    if role in ['admin', 'superadmin']:
        pemulangan_raw = Peminjaman.query.filter_by(status='Approved').order_by(Peminjaman.return_date.asc()).all()
    else:
        pemulangan_raw = Peminjaman.query.filter_by(
            user_id=session.get('user_id'), status='Approved'
        ).order_by(Peminjaman.return_date.asc()).all()
    pemulangan_count = len(pemulangan_raw)

    # Annotate each item with days remaining
    pemulangan_list = []
    for p in pemulangan_raw:
        if p.return_date:
            days_left = (p.return_date.date() - today).days
        else:
            days_left = None
        pemulangan_list.append({'item': p, 'days_left': days_left})

    # --- Tiket Lama (Unsettled tickets before today, User only) ---
    tiket_lama = []
    if role not in ['admin', 'superadmin']:
        tiket_lama = Ticket.query.filter(
            Ticket.user_id == session.get('user_id'),
            db.func.date(Ticket.created_at) < today,
            Ticket.status != 'Closed'
        ).order_by(Ticket.created_at.desc()).all()

    # --- Admin modal lists ---
    all_peminjaman = []
    all_tickets_modal = []
    if role in ['admin', 'superadmin']:
        all_peminjaman = Peminjaman.query.filter(
            Peminjaman.status.in_(['Pending', 'Approved'])
        ).order_by(Peminjaman.created_at.desc()).all()
        all_tickets_modal = Ticket.query.filter(
            Ticket.status != 'Closed'
        ).order_by(Ticket.created_at.desc()).all()

    return render_template('index.html',
        tickets=tickets,
        unassigned_tickets=unassigned_tickets,
        assigned_tickets=assigned_tickets,
        open_count=open_count,
        closed_count=closed_count,
        now=datetime.now(),
        display_name=display_name,
        permohonan_hari_ini=permohonan_hari_ini,
        permohonan_today=permohonan_today,
        tiket_hari_ini=tiket_hari_ini,
        tiket_today=tiket_today,
        pemulangan_count=pemulangan_count,
        pemulangan_list=pemulangan_list,
        all_peminjaman=all_peminjaman,
        all_tickets_modal=all_tickets_modal,
        tiket_lama=tiket_lama
    )

@app.route('/archive')
@login_required
def archive():
    role = session.get('role')
    today = datetime.now().date()
    
    # Filter: (Status is Closed) OR (Status is NOT Closed AND created before today)
    archive_filter = db.or_(
        Ticket.status == 'Closed',
        db.and_(Ticket.status != 'Closed', db.func.date(Ticket.created_at) < today)
    )

    if role in ['admin', 'superadmin']:
        tickets = Ticket.query.filter(archive_filter).order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter(
            Ticket.user_id == session.get('user_id'),
            archive_filter
        ).order_by(Ticket.created_at.desc()).all()
        
    return render_template('archive.html', tickets=tickets)

@app.route('/peminjaman/senarai')
@login_required
def senarai_peminjaman():
    role = session.get('role')
    # All peminjaman excluding Pending (not yet approved)
    if role in ['admin', 'superadmin']:
        rekod = Peminjaman.query.filter(
            Peminjaman.status.in_(['Approved', 'Returned'])
        ).order_by(Peminjaman.id.asc()).all()
    else:
        rekod = Peminjaman.query.filter(
            Peminjaman.user_id == session.get('user_id'),
            Peminjaman.status.in_(['Approved', 'Returned'])
        ).order_by(Peminjaman.id.asc()).all()
    return render_template('senarai_peminjaman.html', rekod=rekod)

@app.route('/pemulangan/senarai')
@login_required
def senarai_pemulangan():
    role = session.get('role')
    from datetime import datetime
    today = datetime.now().date()
    # All Approved (belum pulang) + Returned (dah pulang)
    if role in ['admin', 'superadmin']:
        rekod_raw = Peminjaman.query.filter(
            Peminjaman.status.in_(['Approved', 'Returned'])
        ).order_by(Peminjaman.id.asc()).all()
    else:
        rekod_raw = Peminjaman.query.filter(
            Peminjaman.user_id == session.get('user_id'),
            Peminjaman.status.in_(['Approved', 'Returned'])
        ).order_by(Peminjaman.id.asc()).all()
    rekod = []
    for p in rekod_raw:
        if p.return_date and p.status == 'Approved':
            days_left = (p.return_date.date() - today).days
        else:
            days_left = None
        rekod.append({'item': p, 'days_left': days_left})
    return render_template('senarai_pemulangan.html', rekod=rekod)


@app.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        for_user_id = request.form.get('for_user_id')
        
        if title and description and category:
            attachment_filename = None
            file = request.files.get('attachment')
            if file and file.filename != '' and allowed_file(file.filename):
                from werkzeug.utils import secure_filename
                import os
                attachment_filename = secure_filename(f"ticket_{session.get('user_id')}_{file.filename}")
                file.save(os.path.join(app.config['ATTACHMENT_FOLDER'], attachment_filename))

            # Determine the user_id for the ticket
            ticket_user_id = session.get('user_id')
            if session.get('role') in ['admin', 'superadmin'] and for_user_id:
                try:
                    ticket_user_id = int(for_user_id)
                except ValueError:
                    pass

            new_ticket = Ticket(
                title=title, 
                description=description, 
                category=category,
                attachment=attachment_filename, 
                user_id=ticket_user_id
            )
            db.session.add(new_ticket)
            db.session.commit()
            
            # Send Email Notification
            user = User.query.get(ticket_user_id)
            if user and user.email_address:
                send_email(
                    subject=f"Tiket Baru Diterima: #{new_ticket.id}",
                    recipient=user.email_address,
                    template="new_ticket",
                    ticket=new_ticket,
                    recipient_name=user.full_name or user.username
                )

            flash('Tiket berjaya dihantar!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Sila isi semua ruangan yang wajib.', 'danger')
            
    # Read pre-fill values from URL if any
    prefill_title = request.args.get('title', '')
    prefill_category = request.args.get('category', '')
    prefill_desc = request.args.get('description', '')
    
    users = []
    if session.get('role') in ['admin', 'superadmin']:
        users = User.query.filter(User.role == 'user').order_by(User.full_name.asc()).all()
            
    return render_template('create_ticket.html', 
                           prefill_title=prefill_title,
                           prefill_category=prefill_category,
                           prefill_desc=prefill_desc,
                           users=users)

@app.route('/ticket/<int:id>', methods=['GET'])
@login_required
def view_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Admins and Superadmins can view all tickets, others only their own
    if session.get('role') not in ['admin', 'superadmin'] and ticket.user_id != session.get('user_id'):
        flash('Anda tidak mempunyai kebenaran untuk melihat tiket tersebut.', 'danger')
        return redirect(url_for('dashboard'))
        
    admins = []
    if session.get('role') in ['admin', 'superadmin']:
        admins = User.query.filter(User.role.in_(['admin', 'superadmin'])).all()
        
    return render_template('ticket_detail.html', ticket=ticket, admins=admins)

@app.route('/ticket/<int:id>/close', methods=['POST'])
@login_required
@admin_required
def close_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    ticket.status = 'Closed'
    db.session.commit()
    
    # Notify User via Email
    if ticket.author and ticket.author.email_address:
        send_email(
            subject=f"Tiket #{ticket.id} Selesai",
            recipient=ticket.author.email_address,
            template="ticket_closed",
            ticket=ticket,
            recipient_name=ticket.author.full_name or ticket.author.username
        )

    # In-App Notification
    create_notification(
        ticket.user_id,
        f"Tiket #{ticket.id} telah ditutup.",
        url_for('view_ticket', id=ticket.id)
    )

    flash(f'Tiket #{id} ditandakan sebagai ditutup.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/ticket/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Only author can edit, and only if it's open
    if session.get('user_id') != ticket.user_id:
        flash('Anda tidak dibenarkan mengemaskini tiket ini.', 'danger')
        return redirect(url_for('view_ticket', id=id))
        
    if ticket.status != 'Open':
        flash('Hanya tiket yang masih terbuka boleh dikemaskini.', 'warning')
        return redirect(url_for('view_ticket', id=id))
        
    if request.method == 'POST':
        ticket.title = request.form.get('title')
        ticket.category = request.form.get('category')
        ticket.description = request.form.get('description')
        
        attachment = request.files.get('attachment')
        if attachment and allowed_file(attachment.filename):
            filename = secure_filename(attachment.filename)
            import time
            filename = f"{int(time.time())}_{filename}"
            attachment.save(os.path.join(app.config['ATTACHMENT_FOLDER'], filename))
            ticket.attachment = filename
            
        db.session.commit()
        flash('Tiket berjaya dikemaskini.', 'success')
        return redirect(url_for('view_ticket', id=id))
        
    return render_template('edit_ticket.html', ticket=ticket)

@app.route('/ticket/<int:id>/delete', methods=['POST'])
@login_required
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Only author can delete, and only if it's open
    if session.get('user_id') != ticket.user_id:
        flash('Anda tidak dibenarkan memadam tiket ini.', 'danger')
        return redirect(url_for('view_ticket', id=id))
        
    if ticket.status != 'Open':
        flash('Hanya tiket yang masih terbuka boleh dipadam.', 'warning')
        return redirect(url_for('view_ticket', id=id))
        
    # Delete attachment if exists
    if ticket.attachment:
        try:
            os.remove(os.path.join(app.config['ATTACHMENT_FOLDER'], ticket.attachment))
        except:
            pass
            
    # Delete comments associated with the ticket
    Comment.query.filter_by(ticket_id=ticket.id).delete()
    
    db.session.delete(ticket)
    db.session.commit()
    
    flash('Tiket telah berjaya dipadam.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/ticket/<int:id>/take', methods=['POST'])
@login_required
@admin_required
def take_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Only allow taking if it's currently unassigned
    if not ticket.assigned_to_id and not ticket.proposed_assignee_id:
        ticket.assigned_to_id = session.get('user_id')
        db.session.commit()
        
        assigned_user = User.query.get(session.get('user_id'))
        assigned_name = assigned_user.full_name or assigned_user.username
        
        # Notify the author
        create_notification(
            ticket.user_id,
            f"Tiket #{ticket.id} kini dikendalikan oleh {assigned_name}.",
            url_for('view_ticket', id=ticket.id)
        )
        
        flash(f'Anda telah mengambil alih Tiket #{ticket.id}.', 'success')
    else:
        flash('Tiket ini sudah diambil atau sedang menuggu penerimaan.', 'danger')
        
    return redirect(url_for('view_ticket', id=id))

@app.route('/ticket/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Permission check
    can_comment = False
    u_id = session.get('user_id')
    role = session.get('role')
    
    if u_id == ticket.user_id:
        can_comment = True
    elif ticket.assigned_to_id:
        if u_id == ticket.assigned_to_id:
            can_comment = True
    elif role in ['admin', 'superadmin']:
        can_comment = True
        
    if not can_comment:
        flash('Anda tidak dibenarkan mengulas pada tiket ini.', 'danger')
        return redirect(url_for('view_ticket', id=id))

    content = request.form.get('content')
    attachment = request.files.get('attachment')
    
    attachment_filename = None
    if attachment and allowed_file(attachment.filename):
        filename = secure_filename(attachment.filename)
        # Prefix with timestamp to avoid name collisions
        import time
        filename = f"{int(time.time())}_{filename}"
        attachment.save(os.path.join(app.config['ATTACHMENT_FOLDER'], filename))
        attachment_filename = filename
    
    if content or attachment_filename:
        comment = Comment(
            content=content or "Melampirkan fail.",
            attachment_filename=attachment_filename,
            ticket_id=ticket.id,
            user_id=session.get('user_id')
        )
        db.session.add(comment)
        db.session.commit()
        
        # Email Notification
        # If admin/superadmin comments, notify the author
        # If user comments, notify the assigned admin (if any) or all admins (if unassigned)
        user_role = session.get('role')
        sender_name = session.get('username')
        user_db = User.query.get(session.get('user_id'))
        if user_db:
            sender_name = user_db.full_name or user_db.username

        if user_role in ['admin', 'superadmin']:
            # Notify Author (only if the admin is NOT the author of the ticket)
            if ticket.author and ticket.author.email_address and ticket.user_id != session.get('user_id'):
                send_email(
                    subject=f"Komen Baru pada Tiket #{ticket.id}",
                    recipient=ticket.author.email_address,
                    template="comment_notification",
                    ticket=ticket,
                    comment=comment,
                    recipient_name=ticket.author.full_name or ticket.author.username,
                    sender_name=sender_name
                )
        else:
            # Notify Assigned Admin or all Admins
            recipients = []
            if ticket.assigned_to and ticket.assigned_to.email_address:
                # Don't notify the assigned admin if they are the one commenting (e.g., they are testing as a user)
                if ticket.assigned_to_id != session.get('user_id'):
                    recipients.append(ticket.assigned_to.email_address)
            else:
                admins = User.query.filter(User.role.in_(['admin', 'superadmin'])).all()
                recipients = [a.email_address for a in admins if a.email_address]
            
            for r in recipients:
                send_email(
                    subject=f"Komen Baru daripada Pengguna (Tiket #{ticket.id})",
                    recipient=r,
                    template="comment_notification",
                    ticket=ticket,
                    comment=comment,
                    recipient_name="Admin",
                    sender_name=sender_name
                )

        # In-App Notification (Disabled)


        flash('Komen berjaya ditambah.', 'success')
    else:
        flash('Komen tidak boleh kosong melainkan fail dilampirkan.', 'danger')
        
    return redirect(url_for('view_ticket', id=id))

@app.route('/ticket/<int:id>/update_details', methods=['POST'])
@login_required
def update_ticket_details(id):
    if session.get('role') not in ['admin', 'superadmin']:
        flash('Hanya admin yang boleh menguruskan tiket.', 'danger')
        return redirect(url_for('view_ticket', id=id))
        
    ticket = Ticket.query.get_or_404(id)
    
    # Permission check: Only the assigned admin or proposed admin can edit
    u_id = session.get('user_id')
    if ticket.assigned_to_id and ticket.assigned_to_id != u_id:
        if ticket.proposed_assignee_id != u_id:
            flash('Hanya admin yang mengambil tiket ini boleh mengemas kininya.', 'danger')
            return redirect(url_for('view_ticket', id=id))
    
    new_priority = request.form.get('priority')
    new_assignee_id = request.form.get('assigned_to_id')
    
    changes_made = False
    
    if new_priority and new_priority != ticket.priority:
        ticket.priority = new_priority
        changes_made = True
        
    if new_assignee_id and new_assignee_id != str(ticket.assigned_to_id) and new_assignee_id != str(ticket.proposed_assignee_id):
        if new_assignee_id == 'none':
            ticket.assigned_to_id = None
            ticket.proposed_assignee_id = None
        elif int(new_assignee_id) == session.get('user_id'):
            # Admin assigns to themselves
            ticket.assigned_to_id = session.get('user_id')
            ticket.proposed_assignee_id = None
            
            admin_user = User.query.get(session.get('user_id'))
            admin_name = admin_user.full_name or admin_user.username
            
            # Email Notification
            if ticket.author and ticket.author.email_address:
                send_email(
                    subject=f"Tiket #{ticket.id} Diagih Kepada Admin Baru",
                    recipient=ticket.author.email_address,
                    template="ticket_assigned",
                    ticket=ticket,
                    recipient_name=ticket.author.full_name or ticket.author.username,
                    admin_name=admin_name
                )
            
            # In-App Notification to the user (Disabled)

        else:
            # Assigning to ANOTHER admin -> entering PENDING phase
            ticket.proposed_assignee_id = int(new_assignee_id)
            
            admin_user = User.query.get(session.get('user_id'))
            sender_name = admin_user.full_name or admin_user.username
            
            # In-App Notification to admin (Disabled)

        changes_made = True

    if changes_made:
        db.session.commit()
        flash(f'Butiran tiket #{id} telah dikemas kini.', 'success')
        
    return redirect(url_for('view_ticket', id=id))

@app.route('/ticket/<int:id>/accept_assignment', methods=['POST'])
@login_required
def accept_assignment(id):
    ticket = Ticket.query.get_or_404(id)
    
    if ticket.proposed_assignee_id != session.get('user_id'):
        flash('Anda tidak diberi kebenaran untuk menerima tugasan ini.', 'danger')
        return redirect(url_for('view_ticket', id=id))
        
    ticket.assigned_to_id = session.get('user_id')
    ticket.proposed_assignee_id = None
    db.session.commit()
    
    admin_user = User.query.get(session.get('user_id'))
    admin_name = admin_user.full_name or admin_user.username
    
    # Email Notification
    if ticket.author and ticket.author.email_address:
        send_email(
            subject=f"Tiket #{ticket.id} Diagih Kepada Admin Baru",
            recipient=ticket.author.email_address,
            template="ticket_assigned",
            ticket=ticket,
            recipient_name=ticket.author.full_name or ticket.author.username,
            admin_name=admin_name
        )
    
    # In-App Notification to the user
    create_notification(
        ticket.user_id,
        f"Tiket #{ticket.id} kini dikendalikan oleh {admin_name}.",
        url_for('view_ticket', id=ticket.id)
    )
        
    flash(f"Anda berjaya mengambil alih Tiket #{id}.", 'success')
    return redirect(url_for('view_ticket', id=id))

@app.route('/ticket/<int:id>/accept', methods=['POST'])
@login_required
def accept_ticket(id):
    if session.get('role') not in ['admin', 'superadmin']:
        flash('Hanya admin yang boleh menerima tiket.', 'danger')
        return redirect(url_for('view_ticket', id=id))
        
    ticket = Ticket.query.get_or_404(id)
    ticket.assigned_to_id = session.get('user_id')
    # Update status to 'In Progress' or similar if needed, or leave it as is if 'Open' is fine.
    # We will just mark it as accepted by setting the assignee.
    db.session.commit()
    
    # Notify Author
    if ticket.author and ticket.author.email_address:
        admin_user = User.query.get(session.get('user_id'))
        admin_name = admin_user.full_name or admin_user.username
        send_email(
            subject=f"Tiket #{ticket.id} Diambil Oleh Admin",
            recipient=ticket.author.email_address,
            template="ticket_assigned",
            ticket=ticket,
            recipient_name=ticket.author.full_name or ticket.author.username,
            admin_name=admin_name
        )
    
    # In-App Notification (Disabled)

        
    flash(f'Anda telah menerima tiket #{id}.', 'success')
    return redirect(url_for('view_ticket', id=id))

@app.route('/ticket/<int:id>/reject', methods=['POST'])
@login_required
def reject_ticket(id):
    if session.get('role') not in ['admin', 'superadmin']:
        flash('Hanya admin yang boleh menolak tiket.', 'danger')
        return redirect(url_for('view_ticket', id=id))
        
    ticket = Ticket.query.get_or_404(id)
    ticket.status = 'Rejected'
    db.session.commit()
    
    # Notify Author
    if ticket.author and ticket.author.email_address:
        admin_user = User.query.get(session.get('user_id'))
        admin_name = admin_user.full_name or admin_user.username
        send_email(
            subject=f"Tiket #{ticket.id} Telah Ditolak",
            recipient=ticket.author.email_address,
            template="ticket_assigned", # A general notification template
            ticket=ticket,
            recipient_name=ticket.author.full_name or ticket.author.username,
            admin_name=admin_name
        )
        
    flash(f'Tiket #{id} telah ditolak.', 'danger')
    return redirect(url_for('view_ticket', id=id))

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    user = User.query.get(session.get('user_id'))
    return render_template('profile.html', user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = User.query.get(session.get('user_id'))

    if request.method == 'GET':
        return render_template('change_password.html', user=user)

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not old_password or not new_password or not confirm_password:
        flash('Sila isi semua medan kata laluan.', 'danger')
        return redirect(url_for('change_password'))

    if user.password != old_password:
        flash('Kata laluan lama tidak betul.', 'danger')
        return redirect(url_for('change_password'))

    if new_password != confirm_password:
        flash('Kata laluan baru tidak sepadan. Sila cuba semula.', 'danger')
        return redirect(url_for('change_password'))

    if len(new_password) < 4:
        flash('Kata laluan baru mestilah sekurang-kurangnya 4 aksara.', 'danger')
        return redirect(url_for('change_password'))

    user.password = new_password
    db.session.commit()
    flash('Kata laluan berjaya dikemas kini!', 'success')
    return redirect(url_for('change_password'))

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.get(session.get('user_id'))
    if request.method == 'POST':
        user.phone_number = request.form.get('phone_number')
        user.work_position = request.form.get('work_position')
        user.working_grade = request.form.get('working_grade')
        user.email_address = request.form.get('email_address')
        
        file = request.files.get('profile_picture')
        cropped_data = request.form.get('cropped_image')
        filename = None

        if cropped_data and 'base64,' in cropped_data:
            import base64
            # Extract the base64 part
            header, encoded = cropped_data.split('base64,')
            data = base64.b64decode(encoded)
            
            filename = secure_filename(f"{user.id}_avatar.jpg")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f:
                f.write(data)
        elif file and file.filename != '':
            filename = secure_filename(f"{user.id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
        if filename:
            if user.role in ['admin', 'superadmin']:
                user.profile_picture = filename
                flash('Profil berjaya dikemas kini!', 'success')
            else:
                user.pending_profile_picture = filename
                flash('Permohonan kemas kini gambar profil telah dihantar untuk kelulusan Admin.', 'info')
            
        db.session.commit()
        return redirect(url_for('profile'))


        
    return render_template('edit_profile.html', user=user)

@app.route('/user_roles', methods=['GET', 'POST'])
@login_required
@superadmin_required
def user_roles():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_role = request.form.get('role')
        if user_id and new_role in ['user', 'admin']:
            user = User.query.get(user_id)
            if user and user.role != 'superadmin':
                user.role = new_role
                db.session.commit()
                flash(f"Peranan {user.username} dikemas kini kepada {new_role}.", 'success')
        return redirect(url_for('user_roles'))
        
    users = User.query.filter(User.role != 'superadmin').order_by(User.department, User.username).all()
    
    # Group users by department
    from collections import defaultdict
    grouped_users = defaultdict(list)
    for user in users:
        dept = user.department or 'Tiada Jabatan'
        grouped_users[dept].append(user)
    
    # Sort departments alphabetically, but put 'Tiada Jabatan' last
    sorted_departments = sorted(
        grouped_users.keys(),
        key=lambda d: (d == 'Tiada Jabatan', d)
    )
    
    return render_template('user_roles.html', users=users, grouped_users=grouped_users, sorted_departments=sorted_departments)

@app.route('/pengesahan')
@login_required
@admin_required
def pengesahan():
    pending_profiles = User.query.filter(User.pending_profile_picture != None).all()
    return render_template('pengesahan.html', pending_profiles=pending_profiles)


@app.route('/admin/approve-profile/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_profile_picture(user_id):
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    
    if action == 'approve':
        if user.pending_profile_picture:
            user.profile_picture = user.pending_profile_picture
            user.pending_profile_picture = None
            db.session.commit()
            flash(f'Gambar profil {user.username} telah diluluskan.', 'success')
    elif action == 'reject':
        user.pending_profile_picture = None
        db.session.commit()
        flash(f'Gambar profil {user.username} telah ditolak.', 'danger')
        
    return redirect(url_for('pengesahan'))
    

@app.route('/admin/register-aset', methods=['POST'])
@login_required
@admin_required
def register_aset():
    category = request.form.get('category')
    name = request.form.get('name')
    serial_number = request.form.get('serial_number')
    tag_id = request.form.get('tag_id')
    quantity = request.form.get('quantity', 1)
    
    try:
        quantity = int(quantity)
    except:
        quantity = 1

    if not category:
        flash('Sila pilih kategori aset.', 'danger')
        return redirect(url_for('create_peminjaman'))

    # If name is empty, auto-generate it: Category + Tag ID
    if not name:
        if tag_id:
            name = f"{category} - {tag_id}"
        else:
            # Fallback if no name and no tag_id
            import random
            name = f"{category} - {random.randint(1000, 9999)}"

    # Check if name already exists
    existing = AsetInventory.query.filter_by(name=name).first()
    if existing:
        flash(f'Aset dengan nama "{name}" sudah wujud.', 'warning')
        return redirect(url_for('create_peminjaman'))

    new_asset = AsetInventory(
        category=category,
        name=name,
        serial_number=serial_number,
        tag_id=tag_id,
        quantity=quantity,
        is_available=True if quantity > 0 else False
    )
    db.session.add(new_asset)
    db.session.commit()
    
    flash(f'Aset "{name}" telah didaftarkan dengan kuantiti {quantity}.', 'success')
    return redirect(url_for('create_peminjaman'))



@app.route('/peminjaman/new', methods=['GET', 'POST'])
@login_required
def create_peminjaman():
    from datetime import datetime
    import json
    current_user = User.query.get(session.get('user_id'))
    is_admin = session.get('role') in ['admin', 'superadmin']

    if request.method == 'POST':
        aset = request.form.get('aset')
        lokasi = request.form.get('lokasi')
        lokasi_lain = request.form.get('lokasi_lain')
        purpose = request.form.get('purpose')
        borrow_date_str = request.form.get('borrow_date')
        return_date_str = request.form.get('return_date')

        # Admin can submit on behalf of another user
        if is_admin:
            behalf_user_id = request.form.get('behalf_user_id')
            target_user_id = int(behalf_user_id) if behalf_user_id else session.get('user_id')
        else:
            target_user_id = session.get('user_id')

        if aset and lokasi and purpose and borrow_date_str and return_date_str:
            try:
                borrow_date = datetime.strptime(borrow_date_str, '%Y-%m-%d')
                return_date = datetime.strptime(return_date_str, '%Y-%m-%d') if return_date_str else None

                total_quantity = request.form.get('total_quantity', 1)
                try:
                    total_quantity = int(total_quantity)
                except:
                    total_quantity = 1

                new_peminjaman = Peminjaman(
                    aset=aset,
                    quantity=total_quantity,
                    lokasi=lokasi,
                    lokasi_lain=lokasi_lain,
                    purpose=purpose,
                    borrow_date=borrow_date,
                    return_date=return_date,
                    user_id=target_user_id
                )
                db.session.add(new_peminjaman)
                db.session.commit()

                target_user = User.query.get(target_user_id)
                behalf_name = target_user.full_name or target_user.username if target_user else ''
                if is_admin and target_user_id != session.get('user_id'):
                    flash(f'Permohonan peminjaman bagi pihak {behalf_name} berjaya dihantar!', 'success')
                else:
                    flash('Permohonan peminjaman berjaya dihantar!', 'success')
                return redirect(url_for('dashboard'))
            except ValueError:
                flash('Format tarikh tidak sah.', 'danger')
        else:
            flash('Sila isi semua ruangan yang wajib.', 'danger')

    # Fetch available inventory
    available_assets = AsetInventory.query.filter_by(is_available=True).order_by(AsetInventory.name.asc()).all()
    assets_dict = {}
    for a in available_assets:
        if a.category not in assets_dict:
            assets_dict[a.category] = []
        assets_dict[a.category].append(a.name)

    categories = sorted(assets_dict.keys())

    # Pass all users for admin picker (sorted by name)
    all_users = User.query.order_by(User.full_name.asc()).all() if is_admin else []

    return render_template('create_peminjaman.html',
        current_user=current_user,
        now=datetime.now(),
        assets_data=assets_dict,
        categories=categories,
        all_users=all_users,
        is_admin=is_admin
    )
@app.route('/peminjaman/<int:id>', methods=['GET'])
@login_required
def view_peminjaman(id):
    from models import AsetInventory, PemulanganItem
    peminjaman = Peminjaman.query.get_or_404(id)
    
    # Permission check
    if session.get('role') not in ['admin', 'superadmin'] and peminjaman.user_id != session.get('user_id'):
        flash('Anda tidak mempunyai kebenaran untuk melihat rekod ini.', 'danger')
        return redirect(url_for('dashboard'))
        
    # For admin: pass available assets to assign during approval or update
    available_assets_by_cat = {}
    pre_assigned_items = []
    if session.get('role') in ['admin', 'superadmin'] and peminjaman.status in ['Pending', 'Approved']:
        # Get all actually available assets
        all_available = AsetInventory.query.filter_by(is_available=True).order_by(AsetInventory.name.asc()).all()
        for a in all_available:
            if a.category not in available_assets_by_cat:
                available_assets_by_cat[a.category] = []
            available_assets_by_cat[a.category].append({'id': a.id, 'name': a.name})
        
        # Get currently assigned assets (even if not available because they are assigned to THIS request)
        aset_names = [a.strip() for a in peminjaman.aset.split(',') if a.strip()]
        for name in aset_names:
            if peminjaman.status == 'Approved':
                pre_assigned_items.append(name)
                # Also add back to available list so they can be re-selected if removed in UI
                inv = AsetInventory.query.filter_by(name=name).first()
                if inv:
                    if inv.category not in available_assets_by_cat:
                        available_assets_by_cat[inv.category] = []
                    if not any(item['name'] == name for item in available_assets_by_cat[inv.category]):
                        available_assets_by_cat[inv.category].append({'id': inv.id, 'name': inv.name})
            else:
                inv = AsetInventory.query.filter_by(name=name, is_available=True).first()
                if inv:
                    pre_assigned_items.append(name)

    # Build list of items already returned (for checkbox pre-state)
    returned_items_map = {}  # {item_name: PemulanganItem}
    if peminjaman.status == 'Approved':
        for pi in peminjaman.pemulangan_items:
            returned_items_map[pi.item_name] = pi

    # All individual asset names for this loan
    all_aset_names = [a.strip() for a in peminjaman.aset.split(',') if a.strip()]

    import json
    from datetime import date
    return render_template('peminjaman_detail.html',
        peminjaman=peminjaman,
        available_assets=available_assets_by_cat,
        available_assets_json=json.dumps(available_assets_by_cat),
        pre_assigned_items=pre_assigned_items,
        all_aset_names=all_aset_names,
        returned_items_map=returned_items_map,
        today=date.today().isoformat()
    )

@app.route('/peminjaman/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_peminjaman_status(id):
    peminjaman = Peminjaman.query.get_or_404(id)
    action = request.form.get('action')
    old_status = peminjaman.status
    
    if action == 'approve':
        # Get assets assigned by admin (comma-separated names)
        assigned_assets = request.form.get('assigned_assets', '').strip()

        if not assigned_assets:
            flash('Sila pilih sekurang-kurangnya satu aset untuk diberikan kepada pemohon.', 'danger')
            return redirect(url_for('view_peminjaman', id=id))

        # Update peminjaman.aset with specific items assigned by admin
        aset_list = [a.strip() for a in assigned_assets.split(',') if a.strip()]

        # Check all assigned assets are still available
        unavailable = []
        for a_name in aset_list:
            inv = AsetInventory.query.filter_by(name=a_name).first()
            if not inv or not inv.is_available:
                unavailable.append(a_name)

        if unavailable:
            flash(f'Gagal diluluskan. Aset berikut tidak lagi tersedia: {", ".join(unavailable)}', 'danger')
            return redirect(url_for('view_peminjaman', id=id))

        # Mark assets as unavailable (Decrement quantity)
        for a_name in aset_list:
            inv = AsetInventory.query.filter_by(name=a_name).first()
            if inv:
                inv.quantity = (inv.quantity or 1) - 1
                if inv.quantity <= 0:
                    inv.quantity = 0
                    inv.is_available = False

        peminjaman.aset = ', '.join(aset_list)
        peminjaman.quantity = len(aset_list)
        peminjaman.status = 'Approved'
        peminjaman.approved_by_id = session.get('user_id')
        flash(f'Permohonan telah diluluskan. Aset diberikan: {peminjaman.aset}', 'success')

    elif action == 'update_assets':
        # Get new assets assigned by admin (comma-separated names)
        assigned_assets = request.form.get('assigned_assets', '').strip()

        if not assigned_assets:
            flash('Sila pilih sekurang-kurangnya satu aset.', 'danger')
            return redirect(url_for('view_peminjaman', id=id))

        new_aset_list = [a.strip() for a in assigned_assets.split(',') if a.strip()]
        current_aset_list = [a.strip() for a in peminjaman.aset.split(',') if a.strip()]

        to_add = set(new_aset_list) - set(current_aset_list)
        to_remove = set(current_aset_list) - set(new_aset_list)

        # Check availability for items to add
        unavailable = []
        for a_name in to_add:
            inv = AsetInventory.query.filter_by(name=a_name).first()
            if not inv or not inv.is_available:
                unavailable.append(a_name)

        if unavailable:
            flash(f'Gagal dikemaskini. Aset berikut tidak lagi tersedia: {", ".join(unavailable)}', 'danger')
            return redirect(url_for('view_peminjaman', id=id))

        # Mark new assets as unavailable (Decrement quantity)
        for a_name in to_add:
            inv = AsetInventory.query.filter_by(name=a_name).first()
            if inv:
                inv.quantity = (inv.quantity or 1) - 1
                if inv.quantity <= 0:
                    inv.quantity = 0
                    inv.is_available = False

        # Mark removed assets as available (Increment quantity)
        for a_name in to_remove:
            inv = AsetInventory.query.filter_by(name=a_name).first()
            if inv:
                inv.quantity = (inv.quantity or 0) + 1
                inv.is_available = True

        peminjaman.aset = ', '.join(new_aset_list)
        peminjaman.quantity = len(new_aset_list)
        peminjaman.approved_by_id = session.get('user_id')
        
        db.session.commit()
        flash('Senarai aset telah berjaya dikemaskini.', 'success')
        
    elif action == 'reject':
        peminjaman.status = 'Rejected'
        peminjaman.approved_by_id = session.get('user_id')
        reject_reason = request.form.get('reject_reason')
        if reject_reason:
            peminjaman.reject_reason = reject_reason.strip()
        
        # Free up assets only if it was previously approved
        if old_status == 'Approved':
            aset_list = [a.strip() for a in peminjaman.aset.split(',')]
            for a_name in aset_list:
                inv = AsetInventory.query.filter_by(name=a_name).first()
                if inv:
                    inv.quantity = (inv.quantity or 0) + 1
                    inv.is_available = True
        flash('Permohonan telah ditolak.', 'danger')
        
    elif action == 'return_items':
        # Partial / full per-item return with specific dates
        from models import PemulanganItem
        from datetime import datetime

        all_aset_names = [a.strip() for a in peminjaman.aset.split(',') if a.strip()]
        # Items already recorded as returned
        already_returned = {pi.item_name for pi in peminjaman.pemulangan_items}

        newly_returned = []
        for item_name in all_aset_names:
            checked = request.form.get(f'return_item_{item_name}')
            if checked and item_name not in already_returned:
                date_str = request.form.get(f'return_date_{item_name}', '').strip()
                try:
                    ret_date = datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, TypeError):
                    ret_date = datetime.utcnow()

                pi = PemulanganItem(
                    peminjaman_id=peminjaman.id,
                    item_name=item_name,
                    returned_at=ret_date,
                    processed_by_id=session.get('user_id')
                )
                db.session.add(pi)
                newly_returned.append(item_name)

                # Free up inventory
                inv = AsetInventory.query.filter_by(name=item_name).first()
                if inv:
                    inv.quantity = (inv.quantity or 0) + 1
                    inv.is_available = True

        if not newly_returned:
            flash('Tiada item baharu yang ditandakan sebagai dipulangkan.', 'warning')
            return redirect(url_for('view_peminjaman', id=id))

        # If all items are now returned → mark whole loan as Returned
        db.session.flush()  # so pemulangan_items is up-to-date
        total_returned = {pi.item_name for pi in peminjaman.pemulangan_items}
        if total_returned >= set(all_aset_names):
            peminjaman.status = 'Returned'
            flash(f'Semua aset telah dipulangkan. Status dikemaskini kepada Returned. ({len(newly_returned)} item baharu direkodkan)', 'success')
        else:
            flash(f'{len(newly_returned)} item berjaya direkodkan sebagai dipulangkan.', 'success')
        
    db.session.commit()
    
    # Notification disabled per user request

    
    return redirect(url_for('view_peminjaman', id=id))

@app.route('/peminjaman/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_peminjaman(id):
    peminjaman = Peminjaman.query.get_or_404(id)
    
    # Permission check: Only the author can cancel, and only if it's Pending
    if peminjaman.user_id != session.get('user_id'):
        flash('Anda tidak mempunyai kebenaran untuk membatalkan permohonan ini.', 'danger')
        return redirect(url_for('dashboard'))
        
    if peminjaman.status != 'Pending':
        flash('Hanya permohonan yang masih Pending boleh dibatalkan.', 'warning')
        return redirect(url_for('view_peminjaman', id=id))
        
    peminjaman.status = 'Cancelled'
    db.session.commit()
    flash('Permohonan peminjaman telah dibatalkan.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/pemulangan')
@login_required
def pemulangan():
    if session.get('role') in ['admin', 'superadmin']:
        peminjaman_list = Peminjaman.query.order_by(Peminjaman.created_at.desc()).all()
    else:
        peminjaman_list = Peminjaman.query.filter_by(user_id=session.get('user_id')).order_by(Peminjaman.created_at.desc()).all()
    return render_template('pemulangan.html', peminjaman_list=peminjaman_list)

@app.route('/aset-tidak-ketara')
@login_required
def aset_tidak_ketara():
    softwares = SoftwareLicense.query.order_by(SoftwareLicense.name.asc()).all()
    return render_template('aset_tidak_ketara.html', softwares=softwares)

@app.route('/aset-tidak-ketara/<int:id>')
@login_required
def view_software(id):
    software = SoftwareLicense.query.get_or_404(id)
    # Get all users assigned to this software
    assigned_users = SoftwareUser.query.filter_by(software_id=id).order_by(SoftwareUser.assigned_date.desc()).all()
    used_licenses = len(assigned_users)
    available_licenses = software.total_licenses - used_licenses
    
    # Get users not currently assigned to show in the dropdown
    assigned_user_ids = [su.user_id for su in assigned_users]
    available_users = User.query.filter(User.id.notin_(assigned_user_ids) if assigned_user_ids else True).order_by(User.full_name.asc()).all()
    
    return render_template('software_detail.html', software=software, assigned_users=assigned_users, used_licenses=used_licenses, available_licenses=available_licenses, available_users=available_users)

@app.route('/aset-tidak-ketara/<int:id>/add-user', methods=['POST'])
@login_required
@admin_required
def add_software_user(id):
    software = SoftwareLicense.query.get_or_404(id)
    user_id = request.form.get('user_id')
    
    if not user_id:
        flash('Sila pilih pengguna.', 'warning')
        return redirect(url_for('view_software', id=id))
        
    # Check if there are available licenses
    used_licenses = SoftwareUser.query.filter_by(software_id=id).count()
    if used_licenses >= software.total_licenses:
        flash('Tiada lesen yang tinggal untuk perisian ini.', 'danger')
        return redirect(url_for('view_software', id=id))
        
    # Check if user already assigned
    existing = SoftwareUser.query.filter_by(software_id=id, user_id=user_id).first()
    if existing:
        flash('Pengguna ini sudah mempunyai lesen untuk perisian ini.', 'warning')
        return redirect(url_for('view_software', id=id))
        
    new_assignment = SoftwareUser(
        software_id=id,
        user_id=user_id,
        assigned_by_id=session.get('user_id')
    )
    db.session.add(new_assignment)
    db.session.commit()
    flash('Pengguna telah berjaya ditambah ke senarai lesen.', 'success')
    return redirect(url_for('view_software', id=id))

@app.route('/aset-tidak-ketara/<int:id>/remove-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def remove_software_user(id, user_id):
    assignment = SoftwareUser.query.filter_by(software_id=id, user_id=user_id).first_or_404()
    db.session.delete(assignment)
    db.session.commit()
    flash('Pengguna telah dibuang daripada senarai lesen.', 'success')
    return redirect(url_for('view_software', id=id))

@app.route('/aset-tidak-ketara/<int:id>/add-quota', methods=['POST'])
@login_required
@admin_required
def add_software_quota(id):
    software = SoftwareLicense.query.get_or_404(id)
    try:
        jumlah_lesen = int(request.form.get('jumlah_lesen', 0))
        if jumlah_lesen > 0:
            software.total_licenses += jumlah_lesen
            db.session.commit()
            flash(f'Berjaya menambah {jumlah_lesen} kuota lesen baharu.', 'success')
        else:
            flash('Sila masukkan jumlah lesen yang sah.', 'warning')
    except ValueError:
        flash('Jumlah lesen tidak sah.', 'danger')
        
    return redirect(url_for('view_software', id=id))

@app.route('/aset-tidak-ketara/<int:id>/print-form/<int:user_id>')
@login_required
@admin_required
def print_software_form(id, user_id):
    assignment = SoftwareUser.query.filter_by(software_id=id, user_id=user_id).first_or_404()
    software = SoftwareLicense.query.get_or_404(id)
    
    # Generate application number (e.g., STMAMPU/ATK2026/001)
    year = assignment.assigned_date.strftime('%Y')
    app_no = f"STMAMPU/ATK{year}/{str(assignment.id).zfill(3)}"
    
    return render_template('print_kew_atk_7.html', 
                           assignment=assignment, 
                           software=software,
                           app_no=app_no)

@app.route('/peminjaman/<int:id>/print')
@login_required
def print_peminjaman_form(id):
    peminjaman = Peminjaman.query.get_or_404(id)
    
    # Check authorization: only admin/superadmin or the requester can print
    if session.get('role') not in ['admin', 'superadmin'] and peminjaman.user_id != session.get('user_id'):
        flash('Anda tidak dibenarkan mencetak borang ini.', 'danger')
        return redirect(url_for('peminjaman_list'))
        
    # Generate application number (e.g., STMAMPU/PMJ2026/012)
    year = peminjaman.created_at.strftime('%Y')
    app_no = f"STMAMPU/PMJ{year}/{str(peminjaman.id).zfill(3)}"
    
    return render_template('print_peminjaman_form.html', 
                           peminjaman=peminjaman, 
                           app_no=app_no)


@app.route('/tempahan-bilik', methods=['GET', 'POST'])
@login_required
def tempahan_bilik():
    from datetime import datetime
    if request.method == 'POST':
        title = request.form.get('title')
        purpose = request.form.get('purpose')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        if title and start_date_str and end_date_str:
            try:
                # Expecting format 'YYYY-MM-DDTHH:MM' from datetime-local input
                start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')

                if end_date <= start_date:
                    flash('Waktu tamat mestilah selepas waktu mula.', 'danger')
                else:
                    new_tempahan = TempahanBilik(
                        user_id=session.get('user_id'),
                        title=title,
                        purpose=purpose,
                        start_date=start_date,
                        end_date=end_date,
                        status='Pending'
                    )
                    db.session.add(new_tempahan)
                    db.session.commit()
                    flash('Permohonan tempahan bilik telah dihantar!', 'success')
                    return redirect(url_for('tempahan_bilik'))
            except ValueError:
                flash('Format tarikh/masa tidak sah.', 'danger')
        else:
            flash('Sila isi semua ruangan yang wajib.', 'danger')

    return render_template('tempahan_bilik.html')

@app.route('/api/tempahan-bilik/events')
@login_required
def tempahan_bilik_events():
    tempahan_list = TempahanBilik.query.all()
    events = []
    current_user_id = session.get('user_id')
    is_admin = session.get('role') in ['admin', 'superadmin']
    
    for t in tempahan_list:
        # Visibility Rule: 
        # 1. Approved & Pending are visible to all.
        # 2. Rejected is ONLY visible to Admin or the Requester (owner).
        if t.status == 'Rejected':
            if not is_admin and t.user_id != current_user_id:
                continue

        # Define color based on status
        color = '#ffc107' # Warning/Yellow for Pending
        if t.status == 'Approved':
            color = '#198754' # Success/Green
        elif t.status == 'Rejected':
            color = '#dc3545' # Danger/Red

        events.append({
            'id': t.id,
            'title': t.title,
            'start': t.start_date.isoformat(),
            'end': t.end_date.isoformat(),
            'color': color,
            'extendedProps': {
                'user': t.user.full_name or t.user.username,
                'purpose': t.purpose,
                'status': t.status,
                'approved_by': t.approved_by.full_name or t.approved_by.username if t.approved_by else None,
                'reject_reason': t.reject_reason
            }
        })
    return jsonify(events)

@app.route('/tempahan-bilik/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_tempahan_status(id):
    tempahan = TempahanBilik.query.get_or_404(id)
    action = request.form.get('action')
    
    if action == 'approve':
        tempahan.status = 'Approved'
        tempahan.approved_by_id = session.get('user_id')
        flash('Tempahan bilik telah diluluskan.', 'success')
        
        # Notification disabled

    elif action == 'reject':
        tempahan.status = 'Rejected'
        tempahan.approved_by_id = session.get('user_id')
        reject_reason = request.form.get('reject_reason')
        if reject_reason:
            tempahan.reject_reason = reject_reason.strip()
        flash('Tempahan bilik telah ditolak.', 'danger')
        
        # Notification disabled

    
    db.session.commit()
    return redirect(url_for('tempahan_bilik'))

@app.route('/api/stats')
@login_required
@admin_required
def get_stats():
    from sqlalchemy import func
    
    # 1. Ticket Categories
    ticket_stats = db.session.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()
    ticket_data = {cat: count for cat, count in ticket_stats}
    
    # 2. Asset Status
    asset_stats = db.session.query(AsetInventory.is_available, func.count(AsetInventory.id)).group_by(AsetInventory.is_available).all()
    asset_data = {'Tersedia': 0, 'Dipinjam': 0}
    for is_avail, count in asset_stats:
        if is_avail: asset_data['Tersedia'] = count
        else: asset_data['Dipinjam'] = count
        
    # 3. Room Bookings (Last 6 Months)
    today = datetime.now()
    room_data = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=i*30)
        month_label = month_date.strftime('%b')
        count = TempahanBilik.query.filter(
            db.extract('month', TempahanBilik.start_date) == month_date.month,
            db.extract('year', TempahanBilik.start_date) == month_date.year,
            TempahanBilik.status == 'Approved'
        ).count()
        room_data.append({'month': month_label, 'count': count})
        
    return jsonify({
        'tickets': ticket_data,
        'assets': asset_data,
        'rooms': room_data
    })

@app.route('/report/export/<string:type>')
@login_required
@admin_required
def export_report(type):
    import openpyxl
    from io import BytesIO
    from flask import send_file
    
    wb = openpyxl.Workbook()
    ws = wb.active
    
    filename = f"Laporan_{type}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    if type == 'tickets':
        ws.append(['ID', 'Tajuk', 'Kategori', 'Status', 'Pemohon', 'Tarikh'])
        records = Ticket.query.all()
        for r in records:
            ws.append([r.id, r.title, r.category, r.status, (r.author.full_name or r.author.username) if r.author else 'N/A', r.created_at.strftime('%Y-%m-%d')])
    
    elif type == 'peminjaman':
        ws.append(['ID', 'Aset', 'Lokasi', 'Tujuan', 'Tarikh Pinjam', 'Tarikh Pulang', 'Status', 'Pemohon'])
        records = Peminjaman.query.all()
        for r in records:
            ws.append([r.id, r.aset, r.lokasi, r.purpose, r.borrow_date.strftime('%Y-%m-%d'), r.return_date.strftime('%Y-%m-%d') if r.return_date else '', r.status, (r.user.full_name or r.user.username) if r.user else 'N/A'])
            
    elif type == 'tempahan':
        ws.append(['ID', 'Tajuk', 'Tujuan', 'Mula', 'Tamat', 'Status', 'Pemohon'])
        records = TempahanBilik.query.all()
        for r in records:
            ws.append([r.id, r.title, r.purpose, r.start_date.strftime('%Y-%m-%d %H:%M'), r.end_date.strftime('%Y-%m-%d %H:%M'), r.status, (r.user.full_name or r.user.username) if r.user else 'N/A'])
    
    else:
        return "Invalid report type", 400
        
    # Formatting
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)
        
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/broadcast/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_broadcasts():
    if request.method == 'POST':
        message = request.form.get('message')
        
        if message:
            new_broadcast = Broadcast(
                message=message,
                created_by_id=session.get('user_id'),
                is_active=True
            )
            db.session.add(new_broadcast)
            db.session.commit()
            
            flash('Pengumuman baru telah berjaya diterbitkan.', 'success')
            return redirect(url_for('manage_broadcasts'))
            
    broadcasts = Broadcast.query.order_by(Broadcast.created_at.desc()).all()
    return render_template('manage_broadcasts.html', broadcasts=broadcasts)

@app.route('/broadcast/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_broadcast(id):
    broadcast = Broadcast.query.get_or_404(id)
    broadcast.is_active = not broadcast.is_active
    db.session.commit()
    flash('Status pengumuman telah dikemas kini.', 'info')
    return redirect(url_for('manage_broadcasts'))

@app.route('/broadcast/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_broadcast(id):
    broadcast = Broadcast.query.get_or_404(id)
    db.session.delete(broadcast)
    db.session.commit()
    flash('Pengumuman telah dipadam.', 'warning')
    return redirect(url_for('manage_broadcasts'))

if __name__ == '__main__':
    # Run on port 5020 to avoid conflicts with previous app
    app.run(debug=True, port=5020)
