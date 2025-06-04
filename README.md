# FocusFlow - Task Management Web Application

**FocusFlow** is a web-based task management application with integrated calendar functionality and secure Google OAuth authentication. The application helps users organize their tasks, track due dates, and manage their productivity with an intuitive interface.

---

## 📌 Features

### ✅ Task Management
- Create, edit, and delete tasks with due dates
- Mark tasks as complete or incomplete
- View tasks ordered by due date and completion status
- Visual indicators for overdue tasks (red highlighting)

### 📅 Calendar Integration
- Interactive calendar view showing task distribution
- Clickable dates displaying number of tasks due
- Color-coded dates: red for overdue tasks, normal for current/future tasks
- Day view with detailed task listings for selected dates

### 🔐 Secure Authentication
- Google OAuth 2.0 integration for secure login
- Session management with user profile information
- Secure logout functionality

### 🎨 User Interface
- Responsive design with clean, intuitive interface
- Consistent styling across all pages
- Visual feedback for task status and due dates

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7+
- Google Cloud Platform account for OAuth setup

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FocusFlow
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Google OAuth**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials (Web application)
   - Add `http://127.0.0.1:5001/login/google/authorized` to authorized redirect URIs

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
   GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
   DATABASE_URL=sqlite:///example_test_db.db
   OAUTHLIB_INSECURE_TRANSPORT=1
   ```

5. **Run the application**
   ```bash
   python server.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:5001`

---

## 🛠 Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Google OAuth 2.0
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: SSL support, session management

---

## 📱 Usage

1. **Login**: Click "Login with Google" to authenticate using your Google account
2. **Dashboard**: View all your tasks ordered by due date and completion status
3. **Create Tasks**: Add new tasks with descriptions and due dates
4. **Calendar View**: Navigate to the calendar to see task distribution across dates
5. **Manage Tasks**: Mark tasks as complete/incomplete or delete them as needed

---

## 🔧 Project Structure

```
FocusFlow/
├── server.py              # Main Flask application
├── data.py                # Database models
├── task.py                # Task-related utilities
├── routes/                # Route blueprints
│   ├── calendar_routes.py # Calendar functionality
│   └── todo_routes.py     # Task management routes
├── templates/             # HTML templates
├── static/css/           # Stylesheets
└── requirements.txt      # Python dependencies
```
