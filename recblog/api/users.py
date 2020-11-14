from flask import jsonify, request, url_for, g, current_app
from .. import db
from ..models import User, Post
from . import api


@api.route('/user_account/<int:user_id>')
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.convert_user_json())


