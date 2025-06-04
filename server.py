from flask import Flask, render_template, url_for, redirect, request, session
from data import db, Task
from routes import register_blueprints
from datetime import datetime
from dotenv import load_dotenv
import os
import urllib.parse
import secrets
import requests
import certifi
import ssl

load_dotenv()

# Fix SSL certificate issues on macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Create a custom requests session that bypasses SSL for development
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

session_requests = requests.Session()
# DEVELOPMENT ONLY: Disable SSL verification due to macOS certificate issues
session_requests.verify = False

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example_test_db.db'
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID').strip()
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET').strip()
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

db.init_app(app)
register_blueprints(app)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/login')
def login():
    # Generate a random state for security
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    redirect_uri = url_for('authorize', _external=True)
    print(f"Redirect URI being used: {redirect_uri}")
    
    # Build the authorization URL
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
    # Verify state
    if request.args.get('state') != session.get('oauth_state'):
        return 'Invalid state', 400
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        return 'No code provided', 400
    
    # Exchange code for token
    redirect_uri = url_for('authorize', _external=True)
    
    # Try URL-encoded format
    token_data_encoded = (
        f"code={urllib.parse.quote(code)}"
        f"&client_id={urllib.parse.quote(GOOGLE_CLIENT_ID)}"
        f"&client_secret={urllib.parse.quote(GOOGLE_CLIENT_SECRET)}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&grant_type=authorization_code"
    )
    
    try:
        # Get access token using URL-encoded body
        print(f"Token request URL-encoded: {token_data_encoded}")
        print(f"Client ID: {GOOGLE_CLIENT_ID}")
        print(f"Client Secret (first 10 chars): {GOOGLE_CLIENT_SECRET[:10]}")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        token_response = session_requests.post(
            GOOGLE_TOKEN_URL, 
            data=token_data_encoded, 
            headers=headers
        )
        
        if token_response.status_code != 200:
            print(f"Token error response: {token_response.text}")
            print(f"Status code: {token_response.status_code}")
        
        token_response.raise_for_status()
        tokens = token_response.json()
        
        # Get user info
        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        user_response = session_requests.get(GOOGLE_USERINFO_URL, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Store user info in session
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

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('oauth_state', None)
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user_email = session['user']['email']
    all_tasks = Task.query.filter_by(user_email=user_email).order_by(Task.is_complete.asc(), Task.date.asc()).all()
    today = datetime.today().date()

    for task in all_tasks:
        task.is_overdue = False
        if task.date: # Make sure task.date isn't None
            task_date = task.date 
            task.is_overdue = task_date < today and not task.is_complete
    return render_template('dashboard.html', tasks=all_tasks, user=session['user'])

if __name__ == '__main__':
    # Test SSL connectivity
    print(f"Testing SSL connection to Google...")
    try:
        test_response = session_requests.get('https://www.google.com')
        print(f"SSL test successful: {test_response.status_code}")
    except Exception as e:
        print(f"SSL test failed: {e}")
    
    with app.app_context():
        # db.drop_all()
        db.create_all()
    app.run(debug=True, port=5001)