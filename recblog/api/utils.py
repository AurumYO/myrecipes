from functools import wraps
from flask import g
from flask_jwt_extended import get_jwt_identity
from .errors import forbidden
from ..models import User, Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = User.query.filter_by(email=get_jwt_identity()).first()
            if not user.can(permission):
                return forbidden('Insufficient permission rights.')
            return f(*args, **kwargs)
        return decorated_function
    return decorator
