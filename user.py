from data import db, User

def create_user(email, password):
    new_user = User(email, password)
    db.session.add(new_user)
    db.session.commit()
    return new_user

