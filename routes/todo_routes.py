from flask import Flask, render_template, url_for, redirect, request, Blueprint, session
from data import db, Task
from task import user_create_task, user_mark_complete, user_delete_task
from datetime import datetime

todo_routes = Blueprint('todo_routes', __name__)

@todo_routes.route('/create_task', methods=['POST', 'GET'])
def create_task():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST': 
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')  # e.g. "2025-05-23"
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None

        user_create_task(title, description, date_obj)

        return redirect(url_for('dashboard'))
    else: 
        return render_template('create_task.html')

# Confirm mark complete
@todo_routes.route('/confirm_complete/<int:task_id>')
def confirm_complete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if not task or task.user_email != session['user']['email']:
        return redirect(url_for('dashboard'))
    error = None
    if task.is_complete:
        error = "This task is already marked as complete."
    return render_template('mark_complete.html', task=task, error=error)

# Actually mark as complete
@todo_routes.route('/mark_complete/<int:task_id>', methods=['POST'])
def mark_complete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user_mark_complete(task_id, True)
    return redirect(url_for('dashboard'))

@todo_routes.route('/confirm_mark_incomplete/<int:task_id>')
def confirm_mark_incomplete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if not task or task.user_email != session['user']['email']:
        return redirect(url_for('dashboard'))

    error = None
    if not task.is_complete:
        error = "This task is not marked as complete."

    return render_template('mark_incomplete.html', task=task, error=error)



# Mark incomplete
@todo_routes.route('/mark_incomplete/<int:task_id>', methods=['POST'])
def mark_incomplete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if task and task.is_complete and task.user_email == session['user']['email']:
        task.is_complete = False
        db.session.commit()
    return redirect(url_for('dashboard'))

# Confirm delete
@todo_routes.route('/confirm_delete/<int:task_id>')
def confirm_delete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if not task or task.user_email != session['user']['email']:
        return redirect(url_for('dashboard'))
    return render_template('delete_task.html', task=task)

# Actually delete
@todo_routes.route('/delete/<int:task_id>', methods=['POST'])
def delete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user_delete_task(task_id)
    return redirect(url_for('dashboard'))

@todo_routes.route('/pomodoro')
def pomodoro():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('pomodoro.html')