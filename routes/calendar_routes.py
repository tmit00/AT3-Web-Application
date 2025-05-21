from flask import Blueprint, request, render_template
from datetime import datetime
import calendar
calendar_routes = Blueprint('calendar_routes', __name__)

@calendar_routes.route('/calendar_server')
def calendar_server():
    try:
        # Make sure it's an int to make sure the server is safe
        year = int(request.args.get("year", datetime.now().year))
        month = int(request.args.get("month", datetime.now().month))
    except ValueError:
        return "Invalid Arguments", 400 
    
    month_name = calendar.month_name[month]

    cal = calendar.Calendar().monthdayscalendar(year, month)

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
        month_name=month_name
    )
