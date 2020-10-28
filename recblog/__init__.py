from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from recblog.config import Config


db = SQLAlchemy()

bcrypt = Bcrypt()

admin = Admin()    ## , name='myrecipes', template_mode='bootstrap4'


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


mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    bcrypt.init_app(app)

    admin.init_app(app)

    migrate = Migrate(app, db)

    login_manager.init_app(app)

    mail.init_app(app)


    from recblog.users.routes import users
    from recblog.posts.routes import posts
    from recblog.admins.routes import admins
    from recblog.errors.routes import errors
    from recblog.main.routes import main
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(admins)
    app.register_blueprint(errors)
    app.register_blueprint(main)

    return app
