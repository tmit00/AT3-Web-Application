from flask import Flask, render_template, url_for, redirect, request
from data import db, Task
from routes import register_blueprints



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example_test_db.db'
db.init_app(app)
register_blueprints(app)

@app.route('/', methods=['GET'])
def dashboard():
    all_tasks = Task.query.all()
    return render_template('dashboard.html', tasks=all_tasks)

if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
    app.run(debug=True, port=5001)
