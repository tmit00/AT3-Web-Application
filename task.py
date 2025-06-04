from data import db, Task
from flask import session

def user_create_task(title, description, date):
    user_email = session.get('user', {}).get('email', 'anonymous@example.com')
    new_task = Task(title=title, description=description, date=date, user_email=user_email)
    db.session.add(new_task)
    db.session.commit()
    return new_task

def user_mark_complete(task_id, is_complete=True):
    task = Task.query.get(task_id)
    if task:
        task.is_complete = is_complete
        db.session.commit()

def user_delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()