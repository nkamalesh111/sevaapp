from sevaapp import db, login_manager
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import BIGINT

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    counter = db.Column(db.Integer, nullable=False)
    startdate = db.Column(db.String(10), nullable=True, default=None)
    enddate = db.Column(db.String(10), nullable=True, default=None)
    date = db.Column(db.String(10), nullable=True, default=None)
    address = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(15), nullable=False)
    pincode = db.Column(db.BIGINT(), nullable=False)

    def __repr__(self):
        return f"User('{self.id}')"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    volunteer_id = db.Column(db.Integer)
    action = db.Column(db.String(5), nullable=False)
    pincode = db.Column(db.BIGINT())

    def __repr__(self):
        return f"User('{self.id}')"
