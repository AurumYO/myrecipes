from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length
from flask_pagedown.fields import PageDownField


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
                                                                     ('pie', 'Pie'), ('meat', 'Meat'), ('cake', 'Cake'),
                                                                     ('salad', 'Salad')])

    ingredients = PageDownField('Ingredients: ', validators=[DataRequired()])
    preparation = PageDownField('Process: ', validators=[DataRequired()])
    submit = SubmitField('Post your recipe!')


class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('Submit comment')
