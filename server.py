from flask import Flask, render_template, url_for, redirect, request
from data import db, Task
from routes import register_blueprints
from datetime import datetime



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example_test_db.db'
db.init_app(app)
register_blueprints(app)

@app.route('/', methods=['GET'])
def dashboard():
    all_tasks = Task.query.all()
    today = datetime.today().date()

    for task in all_tasks:
        task.is_overdue = False
        if task.date: # Make sure task.date isn't None
            task_date = task.date 
            task.is_overdue = task_date < today and not task.is_complete
    return render_template('dashboard.html', tasks=all_tasks)

if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
    app.run(debug=True, port=5001)
