import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'try-to-guess-me'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    MYRECBLOG_MAIL_SUBJECT_PREFIX = '[MYRECBLOG]'
    MYRECBLOG_MAIL_SENDER = 'MYRECBLOG admin <myrecblog@demo.com>'

    MYRECBLOG_ADMIN = os.environ.get('MYRECBLOG_ADMIN')
    MYRECBLOG_ADMIN_SWATCH = 'cerulean'

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MYRECBLOG_POSTS_PER_PAGE = 12
    MYRECBLOG_COMMENTS_PER_PAGE = 20
    MYRECBLOG_FOLLOWERS_PER_PAGE = 50


    @staticmethod
    def init_app(app):
        pass

