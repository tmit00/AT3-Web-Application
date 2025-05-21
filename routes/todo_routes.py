from flask import Flask, render_template, url_for, redirect, request, Blueprint
from data import db, Task
from task import user_create_task, user_mark_complete, user_delete_task

todo_routes = Blueprint('todo_routes', __name__)

@todo_routes.route('/create_task', methods=['POST', 'GET'])
def create_task():
    if request.method == 'POST': 
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')

        user_create_task(title, description, priority)

        return redirect(url_for('dashboard'))
    else: 
        return render_template('create_task.html')

# Confirm mark complete
@todo_routes.route('/confirm_complete/<int:task_id>')
def confirm_complete(task_id):
    task = Task.query.get(task_id)
    if not task:
        return redirect(url_for('dashboard'))
    error = None
    if task.is_complete:
        error = "This task is already marked as complete."
    return render_template('mark_complete.html', task=task, error=error)

# Actually mark as complete
@todo_routes.route('/mark_complete/<int:task_id>', methods=['POST'])
def mark_complete(task_id):
    user_mark_complete(task_id)  # Set task.is_complete = True in this function
    return redirect(url_for('dashboard'))

# Confirm delete
@todo_routes.route('/confirm_delete/<int:task_id>')
def confirm_delete(task_id):
    task = Task.query.get(task_id)
    return render_template('delete_task.html', task=task)

# Actually delete
@todo_routes.route('/delete/<int:task_id>', methods=['POST'])
def delete(task_id):
    user_delete_task(task_id)
    return redirect(url_for('dashboard'))