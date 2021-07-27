import os
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuration class provide configuration variables for the application
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'try-to-guess-me'
    JWT_SECRET_KEY = os.environ.get('SECRET_KEY') or 'try-to-guess-me'

    # mail server configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    MYRECBLOG_MAIL_SUBJECT_PREFIX = '[MYRECBLOG]'
    MYRECBLOG_MAIL_SENDER = 'MYRECBLOG admin <myrecblog@demo.com>'


    # SQLALCHEMY basic configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    MYRECBLOG_SLOW_DB_QUERY_TIME = 0.5

    # Pagination configuration
    MYRECBLOG_POSTS_PER_PAGE = 12
    MYRECBLOG_COMMENTS_PER_PAGE = 20
    MYRECBLOG_FOLLOWERS_PER_PAGE = 50
    MYRECBLOG_FOLLOWED_PER_PAGE = 50
    LATEST_PER_PAGE = 4
    RECENT_PER_PAGE = 20

    # set bootswatch theme for Flask Admin 
    FLASK_ADMIN_SWATCH = 'journal'
    MYRECBLOG_ADMIN = os.environ.get('MYRECBLOG_ADMIN')


    
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///'
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    LIVESERVER_PORT = 0


config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
