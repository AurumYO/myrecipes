import os
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_bcrypt import Bcrypt
from flask_pagedown import PageDown
from flask_login import LoginManager
from config import Config
from flask_moment import Moment



# app.config['SECRET_KEY'] = '18ae72b4eb2406d9d1bd524f366c9aaf'

# basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
# app.config['FLASKY_ADMIN'] = 'timelion14@gmail.com'

mail = Mail()
db = SQLAlchemy()

config = Config()
admin = Admin()    ## , name='myrecipes', template_mode='bootstrap4'

bcrypt = Bcrypt()

moment = Moment()

###########################
#### LOGIN CONFIGS #######
#########################

# login_manager = LoginManager()
# # We can now pass in our app to the login manager
# login_manager.init_app(app)
# # Tell users what view to go to when they need to login.
# login_manager.login_view = "users.login"
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'

pagedown = PageDown()

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
# app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')

# app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
# app.config['FLASKY_MAIL_SENDER'] = 'Flasky admin <flasky@demo.com>'


def create_app():
    app = Flask( __name__ )
    app.config.from_object(config)
    config.init_app(app)

    mail.init_app(app)
    db.init_app(app)

    login_manager.init_app(app)

    bcrypt.init_app(app)

    admin.init_app(app)

    pagedown.init_app(app)

    moment.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .users import users as users_blueprint
    app.register_blueprint(users_blueprint)

    from .posts import posts as posts_blueprint
    app.register_blueprint(posts_blueprint)

    from .content_management import admins as admins_blueprint
    app.register_blueprint(admins_blueprint)

    return app
