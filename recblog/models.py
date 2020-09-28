from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from recblog import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def get_reset_token(self, expires_sec=18000):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')


    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"""User('{self.username}', '{self.email}', '{self.image_file}')"""



class Post(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text(500))
    post_image = db.Column(db.String(200), nullable=False, default='default.jpg')

    # additional parameters of the post-recipe, right-side part of the post page
    # # rating = db.Column(db.Integer, default=0)   ## not implemented yet
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    portions = db.Column(db.Integer, nullable=False)
    prep_time = db.Column(db.Integer, nullable=False)

    # type of dish - breakfast, dessert, soup, etc.
    type_category = db.Column(db.String(20), nullable=False)

    # post-recipe ingredients and recipe
    ingredients = db.Column(db.Text, nullable=False)
    preparation = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"""User('{self.title}', '{self.date_posted}')"""

