from flask import Flask
from sqlalchemy import MetaData
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_bcrypt import Bcrypt
from flask_pagedown import PageDown
from flask_login import LoginManager
from config import config
from flask_moment import Moment


naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

mail = Mail()
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))


admin = Admin(name='myrecipes admin', template_mode='bootstrap3') 

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

def create_app(config_name):
    app = Flask( __name__ )
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

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

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app
