from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(128))
    limit = db.Column(db.String(1))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    records = db.relationship('Record', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def __repr__(self):
        return '<User {}>'.format(self.username)  

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    content = db.Column(db.Text)
    source = db.Column(db.String(128))
    hint = db.Column(db.Text)
    ms = db.Column(db.String(128))
    kb = db.Column(db.String(128))
    records = db.relationship('Record', backref='worker', lazy='dynamic')

    def __repr__(self):
        return '<Problem {}>'.format(self.id) 

class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    content = db.Column(db.Text)
    source = db.Column(db.String(128))
    contest_problem = db.relationship('Contest_Problem', backref='list', lazy='dynamic')

    def __repr__(self):
        return '<Contest {}>'.format(self.id)

class Contest_Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'))
    problem_id = db.Column(db.Integer)

    def __repr__(self):
        return '<Contest_Problem {}>'.format(self.id)

class Inform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    content = db.Column(db.Text)
    source = db.Column(db.String(128))

    def __repr__(self):
        return '<Inform {}>'.format(self.id) 

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(50))
    code = db.Column(db.Text)
    timesubmit = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    answer = db.Column(db.String(128))
    ms = db.Column(db.String(128))
    kb = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'))

    def __repr__(self):
        return '<Record {}>'.format(self.id)