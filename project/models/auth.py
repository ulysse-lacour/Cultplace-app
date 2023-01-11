from flask_login import UserMixin
from project.settings import DB_ORM as db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(20))
    company = db.Column(db.String(30))
    super_user = db.Column(db.Boolean, default=False)
