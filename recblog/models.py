from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from markdown import markdown
import bleach
from . import db, login_manager
from recblog.exceptions import ValidationError


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return f"""Role {self.name}"""


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    confirmed = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    location = db.Column(db.String())
    about_me = db.Column(db.Text)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    # for the cascade behavior 'delete-orphan' was chosen as fo association table correct way to delete the entries
    # that point to a record that was deleted
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    # @staticmethod
    # def add_self_follower():
    #     for user in User.query.all():
    #         if not user.is_following_user(user):
    #             user.follow_user(user)
    #             db.session.add(user)
    #             db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()


    def __repr__(self):
        return f"""User('{self.username}', '{self.email}', '{self.image_file}')"""

    def generate_confirmation_token(self, expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def get_reset_token(self, expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def follow_user(self, user):
        if not self.is_following_user(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)

    def stop_follow_user(self, user):
        follow = self.followed.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)

    def is_following_user(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by_user(self, user):
        if user.id is None:
            return False
        return self.follower.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.user_id).filter(Follow.follower_id == self.id)

    def convert_user_json(self):
        json_user = {
            'url': url_for('api.get_user', user_id=self.id),
            'username': self.username,
            'email': self.email,
            'image_file': self.image_file,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'location': self.location,
            'role_id': self.role_id,
            'about_me': self.about_me,
            'last_seen': self.last_seen,
            'followed_posts_url': url_for('api.get_followed_posts', id=self.id),
            'post_count': self.posts.count()
        }
        return json_user


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Model for Posts Recipes
class Post(db.Model, UserMixin):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text(500))
    post_image = db.Column(db.String(200), nullable=False, default='default.jpg')

    # additional parameters of the post-recipe, right-side part of the post page
    rating = db.Column(db.Integer, default=0)   ## not implemented yet
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    portions = db.Column(db.Integer, nullable=False)
    prep_time = db.Column(db.Integer, nullable=False)

    # type of dish - breakfast, dessert, soup, etc.
    type_category = db.Column(db.String(20), nullable=False)

    # post-recipe ingredients and recipe
    ingredients = db.Column(db.Text, nullable=False)
    ingredients_html = db.Column(db.Text, nullable=False)
    preparation = db.Column(db.Text, nullable=False)
    preparation_html = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # one-to-many relationships with Comments table
    comments = db.relationship('Comment', backref='post', lazy='dynamic')  #'dynamic')




    @staticmethod
    def on_changed_ingredients(target, new_value, old_value, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong',
                        'ul', 'h1', 'h2', 'h3', 'p']
        target.ingredients_html = bleach.linkify(bleach.clean(markdown(new_value, output_format='html'),
                                                             tags=allowed_tags, strip=True))

    @staticmethod
    def on_changed_preparation(target, new_value, old_value, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong',
                        'ul', 'h1', 'h2', 'h3', 'p']
        target.preparation_html = bleach.linkify(bleach.clean(markdown(new_value, output_format='html'),
                                                             tags=allowed_tags, strip=True))

    def rate_recipe(self, rate):
        pass

    def convert_post_json(self):
        json_post = {
            'url': url_for('api.get_post', post_id=self.id),
            'title': self.title,
            'description': self.description,
            'post_image': self.post_image,
            'rating': self.rating,
            'date_posted': self.date_posted,
            'portions': self.portions,
            'prep_time': self.prep_time,
            'type_category': self.type_category,
            'ingredients': self.ingredients,
            'ingredients_html': self.ingredients_html,
            'preparation': self.preparation,
            'preparation_html': self.preparation_html,
            'user_url': url_for('api.get_user', user_id=self.user_id),
            'comments_url': url_for('api.get_post', post_id=self.id),
            'comments_count': self.comments.count()
        }

        return json_post

    def __repr__(self):
        return f"""User('{self.title}', '{self.date_posted}')"""

    @staticmethod
    def convert_post_from_json(json_post):
        post_body = json_post.get()
        if post_body is None:
            raise ValidationError('There is no such post!')
        return Post(post=post_body)


db.event.listen(Post.ingredients, 'set', Post.on_changed_ingredients)
db.event.listen(Post.preparation, 'set', Post.on_changed_preparation)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    comment_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    @staticmethod
    def on_changed_comment(target, new_value, old_value, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'strong',
                        'p']
        target.body_html = bleach.linkify(bleach.clean(markdown(new_value, output_format='html'), tags=allowed_tags,
                                                       strip=True))

    def convert_comment_to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id),
            'post_url': url_for('api.get_post', id=self.post_id),
            'body': self.body,
            'body_html': self.body_html,
            'comment_date': self.comment_date,
            'author_url': url_for('api.get_user', id=self.author_id)
        }

    def convert_from_json_comment(comment):
        body = comment.get('body')
        if body is None or body == '':
            raise ValidationError('this post does not have a comment')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_comment)
