from wtforms.fields.choices import SelectField

from app import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(20), nullable=False)
    date_birth = db.Column(db.Date())
    sex = db.Column(db.String(10))
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_url = db.Column(db.String(512))
    is_deleted = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    failure_attempts = db.Column(db.Integer, default=0)
    code = db.Column(db.BigInteger, default=None)
    balances = db.relationship('Balance', backref='owner', lazy=True)
    transfers = db.relationship('TransferHistory', backref='sender', lazy=True)
    complains = db.relationship('Complains', backref='sender', lazy=True)

    def locker(self):
        self.is_active = False
        db.session.commit()

    def reset_activate(self):
        self.is_active = True
        self.failure_attempts = 0
        db.session.commit()


class Balance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class TransferHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now())
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(120), nullable=True)


class Complains(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.String(512), nullable=False)
