from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from flask_login import current_user
from ..models import User, Post


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=24),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, "Username must have only letters, numbers, dots or underscores")])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up!')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This name is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data ).first()
        if user:
            raise ValidationError('This email is taken. Please choose a different one.')


class UpdateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=24)])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'])])
    location = StringField('Location', validators=[Length(min=2, max=24)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Please choose a different username.')


# form for updating youser's email
class UpdateUserEmail(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Email')
    
    # function checks if new email entered in the form has not been assigned to other's user account already
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:raise ValidationError('Please choose a different email.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Request Password Reset')

    def validate_password(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Error has occurred with processing the data. Please check your email and try again.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
