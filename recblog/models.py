from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, url_for, abort
from flask_login import UserMixin, AnonymousUserMixin, current_user
from flask_bcrypt import generate_password_hash, check_password_hash
from markdown import markdown
import bleach
from . import db, login_manager
from recblog.exceptions import ValidationError
from flask_admin.contrib.sqla import ModelView


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.convert_user_json() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
                },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page, **kwargs),
                'next': url_for(endpoint, page=page+1,
                                per_page=per_page, **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page-1,
                                per_page=per_page, **kwargs) if resources.has_prev else None
            }
        }
        return data

class BlacklistToken(db.Model):
    """
    Token Model for storing JWT tokens
    """
    __tablename__ = 'blacklist_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)


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

    def convert_follower_json(self):
        json_user = {
            'follower_url': url_for('api.get_user', user_id=self.follower_id),
            'follower_id': self.follower_id,
            'timestamp': self.timestamp,
        }
        return json_user

    def convert_followed_json(self):
        json_user = {
            'followed_url': url_for('api.get_user', user_id=self.followed_id),
            'followed_id': self.followed_id,
            'timestamp': self.timestamp,
        }
        return json_user


class User(PaginatedAPIMixin, db.Model, UserMixin):
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

    favored_posts = db.relationship('FavoritePosts', backref='liker', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['MYRECBLOG_ADMIN']:
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

    def get_authentication_token(self, expires_sec):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires_sec)
        return s.dumps({'id': self.id}).decode('utf-8')

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

    def generate_email_change_token(self, new_mail, expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'change_email': self.id, 'new_email': new_mail}).decode('utf-8')

    def confirm_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except ValidationError:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        self.email = new_email
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

    @staticmethod
    def verify_authentication_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)
        except:
            return None
        return User.query.get(user_id['id'])

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
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.user_id).filter(Follow.follower_id == self.id)

    def convert_user_json(self, include_email=False):
        json_user = {
            'url': url_for('api.get_user', user_id=self.id),
            'username': self.username,
            'image_file': self.image_file,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'location': self.location,
            'role_id': self.role_id,
            'about_me': self.about_me,
            'last_seen': self.last_seen,
            'followed_posts_url': url_for('api.get_followed_posts', id=self.id),
            'followers_number': self.followers.count(),
            'followed_number': self.followed.count(),
            'post_count': self.posts.count(),
            'comments_total': self.comments.count(),
            'favorite_posts_total': self.favored_posts.count()
        }
        if include_email:
            json_user['email'] = self.email
        return json_user

    # !TODO - add posibility to update profile picture
    def convert_user_from_json(self, data, new_user=False):
        for field in ['username', 'email', 'about_me', 'location']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.password = data['password']
        


# Custom view model for Flask-Admin provides check if user, which is trying to access the Admin navigation menue,
# has permission to acces Admin panel
class RecblogAdmin(ModelView):

    # check if user is authenticated and has Admin role
    # if user is not authenticated and has no Admin role, it is redirected to 'Not found' 404.html route
    def is_accessible(self):
        if current_user.is_authenticated and current_user.can(Permission.ADMIN):
            return True
        else:
            return abort(404)


# Custom view model for Flask-Admin provides check if user, which is trying to access the User view model 
# in the Admin navigation menue, has permission to acces the User view model in Admin panel
class RecblogAdminUser(ModelView):
    # add column to custon searchable filter to User model view in Admin panel
    column_filters = ['role']
    # column_sortable_list = ('role')
    

    # check if user is authenticated and has Admin role
    # if user is not authenticated and has no Admin role, it is redirected to 'Not found' 404.html route
    def is_accessible(self):
        if current_user.is_authenticated and current_user.can(Permission.ADMIN):
            return True
        else:
            return abort(404)


# Custom view model for Flask-Admin provides check if user, which is trying to access the Post view model 
# in the Admin navigation menue, has permission to acces the User view model in Admin panel
class RecblogAdminPost(ModelView):
    # add column to custon searchable list to POst model view in Admin panel
    column_searchable_list = ['user_id']

    # check if user is authenticated and has Admin role
    # if user is not authenticated and has no Admin role, it is redirected to 'Not found' 404.html route
    def is_accessible(self):
        if current_user.is_authenticated and current_user.can(Permission.ADMIN):
            return True
        else:
            return abort(404)


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
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    portions = db.Column(db.String(20), nullable=False)
    recipe_yield = db.Column(db.String(40))

    cook_time = db.Column(db.String(30), nullable=False)
    prep_time = db.Column(db.String(30))
    ready = db.Column(db.String(30))
    # type of dish - breakfast, dessert, soup, etc.
    type_category = db.Column(db.String(20), nullable=False)
    main_ingredient = db.Column(db.String(20))

    # post-recipe ingredients and recipe
    ingredients = db.Column(db.Text, nullable=False)
    ingredients_html = db.Column(db.Text, nullable=False)
    preparation = db.Column(db.Text, nullable=False)
    preparation_html = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # one-to-many relationships with Comments table
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    # rating
    favored = db.relationship('FavoritePosts', backref='post_favorite', lazy='dynamic')

    def __repr__(self):
        return f"""User('{self.title}', '{self.date_posted}')"""


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

    def delete_post_from_favorites(self, user_id):
        favorite = self.favored.filter_by(liker_id=user_id).first()
        if favorite:
            db.session.delete(favorite)

    def is_favored_by_user(self, user):
        if user.id is None:
            return False
        return self.favored.filter_by(liker_id=user.id).first() is not None

    @property
    def post_liked_by_user(self, user, post):
        return FavoritePosts.query.filter_by(liker_id=user.id, post_id=post.id)

    # JSON keys were written in accordance with recommendations for instances of Recipes form by https://schema.org/
    def convert_post_json(self):
        json_post = {
            'url': url_for('api.get_post', post_id=self.id),
            'name': self.title,
            'description': self.description,
            'image': self.post_image,
            'datePublished': self.date_posted,
            'portions': self.portions,
            'recipeYield': self.recipe_yield,
            'cookTime': self.cook_time,
            'prepTime': self.prep_time,
            'ready': self.ready,
            'recipeCategory': self.type_category,
            'main_ingredient': self.main_ingredient,
            'recipeIngredient': self.ingredients,
            'recipeIngredient_html': self.ingredients_html,
            'recipeInstructions': self.preparation,
            'recipeInstructions_html': self.preparation_html,
            'user_url': url_for('api.get_user', user_id=self.user_id),
            'comments_url': url_for('api.get_post', post_id=self.id),
            'comments_count': self.comments.count(),
            'favored': self.favored.count()
        }
        return json_post

    @staticmethod
    def convert_post_from_json(json_post):
        post_title = json_post.get('name')
        if post_title is None or post_title == '':
            raise ValidationError('There is no such post!')
        post_description = json_post.get('description')
        if post_description is None or post_description == '':
            raise ValidationError('There is no such description!')
        post_image = json_post.get('image')
        post_portions = json_post.get('portions')
        if post_portions is None or post_portions == '':
            raise ValidationError('There is no such portion!')
        recipe_yield = json_post.get('recipeYield')
        cook_time = json_post.get('cookTime')
        if cook_time is None or cook_time == '':
            raise ValidationError('You should input some value for cooking time!' )
        prep_time = json_post.get('prepTime')
        ready = json_post.get('ready')
        post_type_category = json_post.get('recipeCategory')
        if post_type_category is None or post_type_category == '':
            raise ValidationError('There is no such type_category!')
        main_ingredient = json_post.get('main_ingredient')
        post_ingredients = json_post.get('recipeIngredient')
        if post_ingredients is None or post_ingredients == '':
            raise ValidationError('There is no such ingredients!')
        post_preparation = json_post.get('recipeInstructions')
        if post_preparation is None or post_preparation == '':
            raise ValidationError('There is no such preparation!')
        return Post(title=post_title, description=post_description, post_image=post_image, portions=post_portions,
                    recipe_yield=recipe_yield, cook_time=cook_time, prep_time=prep_time, ready=ready,
                    type_category=post_type_category, main_ingredient = main_ingredient, ingredients=post_ingredients,
                    preparation=post_preparation)


db.event.listen(Post.ingredients, 'set', Post.on_changed_ingredients)
db.event.listen(Post.preparation, 'set', Post.on_changed_preparation)


# Model for Rating the Post-recipe
class FavoritePosts(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    liker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    like_post = db.Column(db.Integer)
    date_liked = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, user_id, post_id):
        if user_id:
            self.liker_id = user_id
            self.post_id = post_id
            self.like_post = 1

    def __repr__(self):
        return f"""FavoritePosts {self.post_id} liked by user {self.liker_id} with {self.like_post}"""

    def convert_favorites_json(self):
        json_favorites = {
            'parentItem': url_for('api.get_post', post_id=self.post_id),
            'liker_url': url_for('api.get_user', user_id=self.liker_id),
            'like_post': self.like_post,
            'dateliked': self.date_liked
        }
        return json_favorites


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
            'url': url_for('api.get_comment', comment_id=self.id),
            'post_url': url_for('api.get_post', post_id=self.post_id),
            'body': self.body,
            'body_html': self.body_html,
            'comment_date': self.comment_date,
            'author_url': url_for('api.get_user', user_id=self.author_id)
        }
        return json_comment

    def convert_from_json_comment(comment):
        body = comment.get('body')
        if body is None or body == '':
            raise ValidationError('this post does not have a comment')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_comment)
