from flask import Blueprint, request, render_template, session, redirect, url_for
from datetime import datetime, date
import calendar
from data import Task
from collections import defaultdict

calendar_routes = Blueprint('calendar_routes', __name__)

@calendar_routes.route('/calendar_server')
def calendar_server():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    try:
        # Make sure it's an int to make sure the server is safe
        year = int(request.args.get("year", datetime.now().year))
        month = int(request.args.get("month", datetime.now().month))
    except ValueError:
        return "Invalid Arguments", 400 
    
    month_name = calendar.month_name[month]

    cal = calendar.Calendar().monthdayscalendar(year, month)

    #Get all tasks for the month for current user
    user_email = session['user']['email']
    tasks = Task.query.filter_by(user_email=user_email).all()
    tasks_by_day = defaultdict(int)
    overdue_tasks_by_day = defaultdict(int)

    today = date.today()

    for task in tasks:
        if not task.date or task.is_complete:
            continue

        task_date = task.date
        
        if task_date.year == year and task_date.month == month:
            if task_date < today:
                overdue_tasks_by_day[task_date.day] += 1
            else:
                tasks_by_day[task_date.day] += 1

    # Calculate previous and next month
    if month > 1:
        prev_month = month - 1
        prev_year = year
    else:
        prev_month = 12
        prev_year = year - 1
    
    if month < 12:
        next_month = month + 1
        next_year = year
    else:
        next_month = 1
        next_year = year + 1
    
    return render_template(
        "calendar.html", year=year, month=month, calendar=cal,
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
        month_name=month_name, tasks_by_day=tasks_by_day,
        overdue_tasks_by_day=overdue_tasks_by_day
    )

@calendar_routes.route('/day/<int:year>/<int:month>/<int:day>')
def view_day(year, month, day):
    if 'user' not in session:
        return redirect(url_for('index'))
        
    date_obj = datetime(year, month, day).date()
    user_email = session['user']['email']
    tasks = Task.query.filter_by(date=date_obj, user_email=user_email).all()

    return render_template("day_view.html", year=year, month=month, day=day, tasks=tasks)