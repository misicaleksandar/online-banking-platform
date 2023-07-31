from ebanking import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(account_id):
    return Account.query.get(account_id)


class Account(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=25), nullable=False)
    lastname = db.Column(db.String(length=25), nullable=False)
    address = db.Column(db.String(length=30), nullable=False)
    city = db.Column(db.String(length=25), nullable=False)
    country = db.Column(db.String(length=25), nullable=False)
    phone_number = db.Column(db.Integer(), nullable=False, unique=True)
    email = db.Column(db.String(length=30), nullable=False, unique=True)
    password = db.Column(db.String(length=16), nullable=False)
    balance = db.relationship('Balance', backref='balance_account', lazy=True)
    card = db.relationship('Card', backref='card_account', lazy=True)


class Card(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    number = db.Column(db.Integer(), nullable=False)
    name = db.Column(db.String(length=25), nullable=False)
    expiration_day = db.Column(db.String(length=25), nullable=False)
    security_code = db.Column(db.Integer(), nullable=False)
    balance = db.Column(db.Integer(), nullable=False)
    account = db.Column(db.Integer(), db.ForeignKey('account.id'))


class Transaction(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    sender = db.Column(db.String(length=30), nullable=False)
    receiver = db.Column(db.String(length=30), nullable=False)
    amount = db.Column(db.Integer(), nullable=False)
    state = db.Column(db.String(length=30), nullable=False)


class Balance(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    currency = db.Column(db.String(length=30), nullable=False)
    amount = db.Column(db.Integer(), nullable=False)
    account = db.Column(db.Integer(), db.ForeignKey('account.id'))






