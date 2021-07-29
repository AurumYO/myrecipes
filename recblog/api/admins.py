from flask import jsonify, request, url_for, g, current_app, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import extract, func
from .. import db
from ..models import User, Post, Permission, FavoritePosts
from . import api
from .utils import permission_required
from .errors import bad_request, forbidden


# analytics on number of likes per date range
@api.route('/analytics/')
@jwt_required()
@permission_required(Permission.ADMIN)
def posts_likes_analytics():
    date_from = request.json.get("date_from", None)
    date_to = request.json.get("date_to", None)
    date_from = datetime.strptime(date_from, "%Y-%m-%d")
    date_to = datetime.strptime(date_to, "%Y-%m-%d")
    print(date_from, date_to)
    likes_analytics = {}
    while date_from <= date_to:
        likes_per_day = FavoritePosts.query.filter(extract('day', FavoritePosts.date_liked) == date_from.day).count()
        likes_analytics[date_from.strftime("%m/%d/%Y")] = f"recieved {likes_per_day} likes"
        print(date_from)
        date_from += timedelta(days=1)
    print(likes_analytics)
    return jsonify(likes_analytics), 200
