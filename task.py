from data import db, Task
from flask import session

def get_user_email():
    return session.get('user', {}).get('email', 'anonymous@example.com')

def user_create_task(title, description, date):
    user_email = get_user_email()
    new_task = Task(title=title, description=description, date=date, user_email=user_email)
    db.session.add(new_task)
    db.session.commit()
    return new_task

def user_mark_complete(task_id, is_complete=True):
    user_email = get_user_email()
    task = Task.query.get(task_id)

    if task and task.user_email == user_email:
        task.is_complete = is_complete
        db.session.commit()

def user_delete_task(task_id):
    user_email = get_user_email()
    task = Task.query.get(task_id)

    if task and task.user_email == user_email:
        db.session.delete(task)
        db.session.commit()
