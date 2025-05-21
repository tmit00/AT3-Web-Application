from flask import Flask, render_template, url_for, redirect, request, Blueprint
from data import db, Task
from task import user_create_task, user_update_task, user_delete_task

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

@todo_routes.route('/update_task', methods=['POST', 'GET'])
def update_task():
    if request.method == 'POST': 
        task_id = request.form.get('id')
        user_update_task(task_id)

        return redirect(url_for('dashboard'))
    else:
         return render_template('update_task.html')

@todo_routes.route('/delete_task', methods=['POST', 'GET'])
def delete_task():
    if request.method == 'POST':
        task_id = request.form.get('id')
        user_delete_task(task_id)

        return redirect(url_for('dashboard'))
    else:
        return render_template('delete_task.html')