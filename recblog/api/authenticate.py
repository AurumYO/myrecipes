from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from recblog.models import User
from .. import bcrypt
from . import api
from recblog.api.errors import unauthorized, forbidden

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email, password):
    if email == '':
        return False
    if password == '':
        g.current_user = User.check_password(password)
        return g.current_user is not None
    user = User.query.filter_by(email=email).first()
    if not user:
        return False
    g.current_user = user
    return g.current_user.check_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')

