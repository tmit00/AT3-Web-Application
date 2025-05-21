from .calendar_routes import calendar_routes
from .todo_routes import todo_routes

def register_blueprints(app):
    app.register_blueprint(calendar_routes)
    app.register_blueprint(todo_routes)