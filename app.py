from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# -------------------------
# FILE SETUP (SAFE)
# -------------------------
app.config['UPLOAD_FOLDER'] = 'static/img/profiles'
app.config['ATTACHMENT_FOLDER'] = 'static/img/attachments'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ATTACHMENT_FOLDER'], exist_ok=True)


# -------------------------
# DISABLE DB COMPLETELY
# -------------------------
# db.init_app(app)
# ALL DATABASE FUNCTIONS REMOVED FOR DEMO


# -------------------------
# SAFE HELPERS
# -------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# -------------------------
# LOGIN DECORATORS (SAFE)
# -------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') not in ['admin', 'superadmin']:
            flash('Admin only area', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapper


# -------------------------
# HOME DASHBOARD (UI ONLY)
# -------------------------
@app.route('/')
@login_required
def dashboard():
    return render_template('index.html',
        tickets=[],
        open_count=0,
        closed_count=0,
        display_name=session.get('user', 'User'),
        permohonan_hari_ini=0,
        tiket_hari_ini=0
    )


# -------------------------
# AUTH (MOCK ONLY)
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['logged_in'] = True
        session['user'] = request.form.get('username', 'demo')
        session['role'] = 'user'
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register')
def register():
    return render_template('register.html')


# -------------------------
# TICKET VIEW (STATIC ONLY)
# -------------------------
@app.route('/ticket/new')
@login_required
def create_ticket():
    return render_template('create_ticket.html')


@app.route('/ticket/<int:id>')
@login_required
def view_ticket(id):
    return render_template('ticket_detail.html', ticket=None)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=session.get('user'))


@app.route('/change-password')
@login_required
def change_password():
    return render_template('change_password.html')

    # -----------------------------
# PASSWORD / PROFILE (UI ONLY)
# -----------------------------

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(new_password) < 4:
            flash('Kata laluan baru mestilah sekurang-kurangnya 4 aksara.', 'danger')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('Kata laluan tidak sepadan.', 'danger')
            return redirect(url_for('change_password'))

        flash('Kata laluan berjaya dikemas kini (demo mode).', 'success')
        return redirect(url_for('change_password'))

    return render_template('change_password.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=session.get('user'))


@app.route('/profile/edit')
@login_required
def edit_profile():
    return render_template('edit_profile.html')


# -----------------------------
# USER ROLES (DEMO ONLY)
# -----------------------------
@app.route('/user_roles')
@login_required
def user_roles():
    return render_template('user_roles.html', users=[])


# -----------------------------
# ASSET / INVENTORY (DEMO ONLY)
# -----------------------------
@app.route('/aset-tidak-ketara')
@login_required
def aset_tidak_ketara():
    return render_template('aset_tidak_ketara.html', softwares=[])


@app.route('/peminjaman')
@login_required
def peminjaman():
    return render_template('pemulangan.html', peminjaman_list=[])


# -----------------------------
# ROOM BOOKING (STATIC)
# -----------------------------
@app.route('/tempahan-bilik')
@login_required
def tempahan_bilik():
    return render_template('tempahan_bilik.html')


@app.route('/api/tempahan-bilik/events')
@login_required
def tempahan_bilik_events():
    return jsonify([])


# -----------------------------
# STATS (EMPTY FOR DEMO)
# -----------------------------
@app.route('/api/stats')
@login_required
def get_stats():
    return jsonify({
        "tickets": {},
        "assets": {"Tersedia": 0, "Dipinjam": 0},
        "rooms": []
    })


# -----------------------------
# EXPORT (DISABLED)
# -----------------------------
@app.route('/report/export/<string:type>')
@login_required
def export_report(type):
    return "Export disabled in demo mode", 200


# -----------------------------
# BROADCAST (STATIC)
# -----------------------------
@app.route('/broadcast/manage')
@login_required
def manage_broadcasts():
    return render_template('manage_broadcasts.html', broadcasts=[])


# -----------------------------
# MAIN RUN (IMPORTANT FOR VERCEL)
# -----------------------------
# REMOVE app.run() for Vercel