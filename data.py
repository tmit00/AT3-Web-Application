from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, nullable=True)
    is_complete = db.Column(db.Boolean, default=False)

    def __init__(self, title, description=None, date=None):
        self.title = title
        self.description = description
        self.date = date
        self.is_complete = False