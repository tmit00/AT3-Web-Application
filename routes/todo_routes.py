from flask import Flask, render_template, url_for, redirect, request, Blueprint, session, jsonify
from data import db, Task
from task import user_create_task, user_mark_complete, user_delete_task
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import chatbot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chatbot import chatbot_instance

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

# Mark as complete (instant action)
@todo_routes.route('/mark_complete/<int:task_id>', methods=['POST'])
def mark_complete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if not task or task.user_email != session['user']['email']:
        return redirect(url_for('dashboard'))
    
    if not task.is_complete:
        user_mark_complete(task_id, True)
    
    return redirect(url_for('dashboard'))

# Mark incomplete (instant action)
@todo_routes.route('/mark_incomplete/<int:task_id>', methods=['POST'])
def mark_incomplete(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if not task or task.user_email != session['user']['email']:
        return redirect(url_for('dashboard'))
    
    if task.is_complete:
        task.is_complete = False
        db.session.commit()
    
    return redirect(url_for('dashboard'))

# Delete task (instant action)
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

@todo_routes.route('/pomodoro/games')
def pomodoro_games():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('games.html')

@todo_routes.route('/chatbot')
def chatbot():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chatbot.html')

@todo_routes.route('/chatbot/send_message', methods=['POST'])
def send_chatbot_message():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        response_data = chatbot_instance.send_message(message)
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': f'Error processing message: {str(e)}'}), 500

@todo_routes.route('/chatbot/clear_history', methods=['POST'])
def clear_chatbot_history():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        chatbot_instance.clear_history()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'Error clearing history: {str(e)}'}), 500

@todo_routes.route('/chatbot/history', methods=['GET'])
def get_chatbot_history():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        history = chatbot_instance.get_history()
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': f'Error getting history: {str(e)}'}), 500

@todo_routes.route('/chatbot/metadata', methods=['GET'])
def get_chatbot_metadata():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        metadata = chatbot_instance.get_metadata()
        return jsonify(metadata)
    except Exception as e:
        return jsonify({'error': f'Error getting metadata: {str(e)}'}), 500