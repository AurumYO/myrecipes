from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length
from flask_pagedown.fields import PageDownField


class PostForm(FlaskForm):
    title = StringField('Recipe title', validators=[DataRequired(), Length(min=3, max=50)])
    description = TextAreaField('Short description or story', validators=[DataRequired()])
    post_picture = FileField('Upload Recipe Picture', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'])])
    # form fields for additional parameters of the post-recipe, right-side part of the post page
    portions = SelectField('Select number of portions: ', choices=[('1','1'), ('2','2'), ('3', '3'), ('4', '4'),
                                                                   ('5', '5'), ('6', '6'), ('8', '8'), ('10', '10'),
                                                                   ('12', '12'), ('16', '16'), ('24', '24')])
    recipe_yield = StringField('Recipe yield', validators=[Length(max=30)],
                               description='For example: 1 loaf or 700 ml.')
    cook_time = StringField('Time of cooking, minutes: ', validators=[DataRequired()])
    prep_time = StringField('Time of preparation, minutes: ',
                            description='Can be time of sitting in the fridge, baking, etc...')
    ready_in = StringField('Ready in: ', description="Can be: 'after 24 hour in the fridge', or 'After stops bubbling'")
    # type of dish - breakfast, dessert, soup, etc
    type_category = SelectField('Select type of recipe: ',
                                choices=[('appetizer', 'Appetizers'), ('alcohol', 'Alcohol & cocktails'),
                                         ('bread', 'Bread'), ('breakfast','Breakfast'), ('cake', 'Cake'),
                                         ('casserole', 'Casserole'), ('chicken', 'Chicken'), ('cookies', 'Cookies'),
                                         ('desserts', 'Desserts'), ('dinner', 'Dinner'), ('lunch', 'Lunch'),
                                         ('main course', 'Main course'), ('non-alcohol', 'Non-alcohol Drink'),
                                         ('pasta', 'Pasta'), ('pie', 'Pies'), ('preserves', 'Preserves'),
                                         ('salad', 'Salad'), ('sauce', 'Sauces & Condiments'), ('side', 'Side dish'),
                                         ('smoothie', 'Smoothie'), ('snack', 'Snacks'), ('soup','Soup & stew'),
                                         ('vegan', 'Vegan & Vegetarian')])
    main_ingredient = SelectField('Select main ingredients: ',
                                          choices=[('beef', 'Beef'), ('cheese', 'Cheese'), ('cereal', 'Cereal'),
                                                   ('chicken', 'Chicken'), ('chocolate', 'Chocolate'), ('eggs', 'Eggs'),
                                                   ('fish', 'Fish'), ('flour', 'Flour'), ('fruit', 'Fruits'),
                                                   ('lamb', 'Lamb'), ('meat', 'Meat, other'), ('milk', 'Milk'),
                                                   ('mushroom', 'Mushrooms'), ('pasta', 'Pasta'), ('pork', 'Pork'),
                                                   ('sausage', 'Sausage'), ('seafood', 'Seafood'), ('turkey', 'Turkey'),
                                                   ('vegetables', 'Vegetables')])
    ingredients = PageDownField('Ingredients: ', validators=[DataRequired()])
    preparation = PageDownField('Process: ', validators=[DataRequired()])
    submit = SubmitField('Post your recipe!')


class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('Submit comment')
