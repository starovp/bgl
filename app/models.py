from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from app import db, login
from hashlib import md5

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    displayname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def avatar(self, size):
        digest = md5(self.displayname.lower().encode('utf-8')).hexdigest()
        return 'https://api.adorable.io/avatars/%s/%s.png'%(size, digest)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.id)

class Match(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    game = db.Column(db.String(48))
    players = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    winner = db.Column(db.String(32))
    skill =  db.Column(db.Integer)

    def __repr__(self):
        return '<Match {}>'.format(self.id)

    def set_skill(self):
        self.skill = 1

class Record(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    mid = db.Column(db.Integer)
    player = db.Column(db.String(32))

    def __repr__(self):
        return '<Record {}>'.format(self.id)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))