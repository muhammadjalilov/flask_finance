from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import FloatField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from app.models import User


class RegistrationForm(FlaskForm):
    fullname = StringField("Fullname", validators=[DataRequired(), Length(min=2, max=32)])
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=32)])
    birth_date = DateField('Birth Date', validators=[DataRequired()])
    sex = SelectField('Sex', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(),
                                                                     EqualTo('password',
                                                                             'Password and Confirm Password must be match')])
    image = FileField('Image',
                      validators=[FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'File must be image!!!')])
    submit = SubmitField('Sign Up', validators=[DataRequired()])

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('This email already taken.Please choose another one')

    def validate_username(self, username):
        card = User.query.filter_by(username=username.data).first()
        if card:
            raise ValidationError('This username number already taken.Please choose another one')


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LogIn", validators=[DataRequired()])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError('User not found')


class AddBalance(FlaskForm):
    amount = FloatField('Amount of money', validators=[DataRequired()])
    submit = SubmitField("Add", validators=[DataRequired()])


class TransferMoney(FlaskForm):
    receiver = IntegerField('Receiver ID', validators=[DataRequired()])
    amount = FloatField('Amount of money', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField("Send", validators=[DataRequired()])


class TransferHistoryForm(FlaskForm):
    start_period = DateField('Start date', validators=[DataRequired()])
    end_period = DateField('End date', validators=[DataRequired()])
    submit = SubmitField("Show", validators=[DataRequired()])


class DeleteForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Delete Account", validators=[DataRequired()])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError('User not found')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if not email:
            raise ValidationError('This email not found')
