from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError
from ebanking.models import Account


class Register(FlaskForm):
    def validate_phone_number(self, phone_number_to_check):
        account = Account.query.filter_by(phone_number=phone_number_to_check.data).first()
        if account:
            raise ValidationError('Another account is already using this phone number.')

    def validate_email(self, email_to_check):
        account = Account.query.filter_by(email=email_to_check.data).first()
        if account:
            raise ValidationError('Another account is already using this email address.')

    name = StringField(label='Name:', validators=[Length(min=3, max=25), DataRequired()])
    lastname = StringField(label='Lastname:', validators=[Length(min=3, max=25), DataRequired()])
    address = StringField(label='Address:', validators=[Length(min=3, max=30), DataRequired()])
    city = StringField(label='City:', validators=[Length(min=3, max=25), DataRequired()])
    country = StringField(label='Country:', validators=[Length(min=3, max=25), DataRequired()])
    phone_number = StringField(label='Phone number:', validators=[Length(min=3, max=30), DataRequired()])
    email = StringField(label='Email:', validators=[Length(min=3, max=30), Email(), DataRequired()])
    password = PasswordField(label='Password:', validators=[Length(min=6, max=16), DataRequired()])
    confirm = PasswordField(label='Confirm password:', validators=[EqualTo('password'), DataRequired()])
    submit = SubmitField(label='Create account')


class Login(FlaskForm):
    email = StringField(label='Email:', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')


class Settings(FlaskForm):
    name = StringField(label='Name:', validators=[Length(min=3, max=25), DataRequired()])
    lastname = StringField(label='Lastname:', validators=[Length(min=3, max=25), DataRequired()])
    address = StringField(label='Address:', validators=[Length(min=3, max=30), DataRequired()])
    city = StringField(label='City:', validators=[Length(min=3, max=25), DataRequired()])
    country = StringField(label='Country:', validators=[Length(min=3, max=25), DataRequired()])
    phone_number = StringField(label='Phone number:', validators=[Length(min=3, max=30), DataRequired()])
    email = StringField(label='Email:', validators=[Length(min=3, max=30), Email(), DataRequired()])
    password = StringField(label='Password:', validators=[Length(min=6, max=16), DataRequired()])
    confirm = StringField(label='Confirm password:', validators=[EqualTo('password'), DataRequired()])
    submit = SubmitField(label='Update')


class Verify(FlaskForm):
    number = StringField(label='Number:', validators=[Length(min=16, max=16), DataRequired()])
    name = StringField(label='Name:', validators=[DataRequired()])
    expiration_day = StringField(label='Expiration day:', validators=[DataRequired()])
    security_code = StringField(label='Security code:', validators=[Length(min=3, max=3), DataRequired()])
    submit = SubmitField(label='Verify')


class Deposit(FlaskForm):
    amount = IntegerField(label='Amount:', validators=[DataRequired()])
    submit = SubmitField(label='Deposit')


class TransactionForm(FlaskForm):
    select = SelectField(label='Select an option:', choices=[('1', 'Bank account'), ('2', 'Card')],
                         validators=[DataRequired()])
    to = StringField(label='To:', validators=[DataRequired()])
    amount = IntegerField(label='Amount:', validators=[DataRequired()])
    submit = SubmitField(label='Send')


class ExchangeForm(FlaskForm):
    amount = IntegerField(label='Enter amount', validators=[DataRequired()])
    submit = SubmitField(label='Exchange')