import os
import urllib.parse
import secrets
import requests
import certifi
import ssl
from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from datetime import datetime, date
from data import db, Task, User
from routes import register_blueprints
from task import api_bp

# Load environment variables
load_dotenv()

# macOS SSL Fixes
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Disable SSL warnings in development
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
session_requests = requests.Session()
session_requests.verify = False  # Development only

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///example_test_db.db')

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure CSRF to accept tokens from X-CSRFToken header for AJAX requests
app.config['WTF_CSRF_TIME_LIMIT'] = None  # Optional: remove time limit
app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']

# Google OAuth config
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID').strip()
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET').strip()
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Init DB and routes
db.init_app(app)
register_blueprints(app)

# Register API blueprint for tasks
app.register_blueprint(api_bp)

# Home route
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# Google OAuth login
@app.route('/login')
def login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    redirect_uri = url_for('authorize', _external=True)
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/login/google/authorized')
def authorize():
    if request.args.get('state') != session.get('oauth_state'):
        return 'Invalid state', 400

    code = request.args.get('code')
    if not code:
        return 'No code provided', 400

    redirect_uri = url_for('authorize', _external=True)
    token_data_encoded = (
        f"code={urllib.parse.quote(code)}"
        f"&client_id={urllib.parse.quote(GOOGLE_CLIENT_ID)}"
        f"&client_secret={urllib.parse.quote(GOOGLE_CLIENT_SECRET)}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&grant_type=authorization_code"
    )

    try:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        token_response = session_requests.post(GOOGLE_TOKEN_URL, data=token_data_encoded, headers=headers)
        token_response.raise_for_status()
        tokens = token_response.json()

        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        user_response = session_requests.get(GOOGLE_USERINFO_URL, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()

        # Ensure user exists in DB
        user = User.query.get(user_info['email'])
        if not user:
            user = User(email=user_info['email'])  # No password for OAuth
            db.session.add(user)
            db.session.commit()

        session['user'] = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture')
        }

        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"OAuth Error: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('index'))

# Manual registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST': 
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if User.query.get(email):
            flash("Email is already registered.")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        session['user'] = {
            'email': email,
            'name': email.split('@')[0],
            'picture': None
        }
        return redirect(url_for("dashboard"))

    return render_template("register.html")

# Manual login
@app.route('/login/manual', methods=['GET', 'POST'])
def manual_login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.get(email)

        if user and user.password == password:
            session['user'] = {
                'email': email,
                'name': email.split('@')[0],
                'picture': None
            }
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.")
            return render_template("login.html")

    return render_template("login.html")

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('oauth_state', None)
    return redirect(url_for('index'))

# --- Pomodoro Stats Tracking ---
def get_stats_for_user(user_email):
    # Store stats in session for simplicity (could use DB for persistence)
    stats = session.get('pomodoro_stats', {})
    today_str = str(date.today())
    user_stats = stats.get(user_email, {})
    today_stats = user_stats.get(today_str, {"pomodoros": 0, "focus_minutes": 0})
    return today_stats

def increment_pomodoro_stat(user_email, minutes):
    stats = session.get('pomodoro_stats', {})
    today_str = str(date.today())
    user_stats = stats.get(user_email, {})
    today_stats = user_stats.get(today_str, {"pomodoros": 0, "focus_minutes": 0})
    today_stats["pomodoros"] += 1
    today_stats["focus_minutes"] += minutes
    user_stats[today_str] = today_stats
    stats[user_email] = user_stats
    session['pomodoro_stats'] = stats

@app.route('/api/pomodoro/complete', methods=['POST'])
def pomodoro_complete():
    if 'user' not in session:
        return jsonify({"error": "Not logged in"}), 401
    user_email = session['user']['email']
    minutes = int(request.form.get('minutes', 25))
    increment_pomodoro_stat(user_email, minutes)
    return jsonify({"success": True})

# Dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))

    user_email = session['user']['email']
    all_tasks = Task.query.filter_by(user_email=user_email).order_by(Task.is_complete.asc(), Task.date.asc()).all()
    today = datetime.today().date()

    for task in all_tasks:
        task.is_overdue = False
        if task.date:
            task.is_overdue = task.date < today and not task.is_complete

    # Get today's stats
    today_stats = get_stats_for_user(user_email)
    pomodoros_today = today_stats.get("pomodoros", 0)
    focus_minutes_today = today_stats.get("focus_minutes", 0)

    return render_template(
        'dashboard.html',
        tasks=all_tasks,
        user=session['user'],
        pomodoros_today=pomodoros_today,
        focus_minutes_today=focus_minutes_today
    )

# Run server
if __name__ == '__main__':
    print(f"Testing SSL connection to Google...")
    try:
        test_response = session_requests.get('https://www.google.com')
        print(f"SSL test successful: {test_response.status_code}")
    except Exception as e:
        print(f"SSL test failed: {e}")

    with app.app_context():
        # db.drop_all()  # Uncomment to reset the database
        db.create_all()

    app.run(debug=True, port=5001, use_reloader=True)
