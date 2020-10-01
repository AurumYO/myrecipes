from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from recblog.models import User, Post
from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=5),
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
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Please choose a different username.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Please choose a different email.')


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



class PostForm(FlaskForm):
    title = StringField('Recipe title', validators=[DataRequired(), Length(min=3, max=50)])
    description = TextAreaField('Short description or story', validators=[DataRequired()])
    post_picture = FileField('Upload Recipe Picture', validators=[FileAllowed(['jpg', 'png'])])

    # # form fields for additional parameters of the post-recipe, right-side part of the post page
    portions = IntegerField('Number of portions: ', validators=[DataRequired()])
    prep_time = StringField('Time of cooking, minutes: ', validators=[DataRequired()])

    # type of dish - breakfast, dessert, soup, etc
    type_category = SelectField('Select type of recipe: ', choices=[('brkf','Breakfast recipe'),
                                                                     ('soup','Soup recipe'), ('chkn', 'Chicken recipe'),
                                                                     ('pasta', 'Pasta recipe'), ('maindish', 'Main Dish'),
                                                                     ('noalcdr', 'Non Alcohol Drink'), ('alcdr', 'Alcohol Drink'),
                                                                     ('seaf', 'Seafood'), ('fish', 'Fish'), ('brd', 'Bread'),
                                                                     ('pie', 'Pie'), ('meet', 'Meat'), ('cake', 'Cake'),
                                                                     ('salad', 'Salad')])

    ingredients = TextAreaField('Ingredients: ', validators=[DataRequired()])
    preparation = TextAreaField('Process: ', validators=[DataRequired()])
    submit = SubmitField('Post your recipe!')
