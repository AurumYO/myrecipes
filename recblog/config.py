import os

class Config:
    # SECRET_KEY = '18ae72b4eb2406d9d1bd524f366c9aaf'

    SECRET_KEY = os.environ.get('SECRET_KEY')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    basedir = os.path.abspath(os.path.dirname( __file__ ) )
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ADMIN_SWATCH = 'cerulean'
    FLASKY_ADMIN = 'timelion14@gmail.com'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get( 'EMAIL_USER' )
    MAIL_PASSWORD = os.environ.get( 'EMAIL_PASS' )

    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky admin <flasky@demo.com>'
