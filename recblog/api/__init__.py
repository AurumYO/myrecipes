from flask import Blueprint

api = Blueprint('api', __name__)

from recblog.api import authenticate, admins, errors, posts, users
