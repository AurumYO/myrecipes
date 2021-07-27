from flask import g, request, jsonify
from flask_jwt_extended import create_access_token
from recblog.models import User
from . import api
from recblog.api.errors import unauthorized, forbidden


@api.route("/login", methods=["POST"])
def login():
    
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user = User.query.filter_by(email=email).first()
    if user is None:
        # the user was not found on the database
        return jsonify({"msg": "Wrong username or password"}), 401
    password = user.check_password(password)
    if not password:
        # the incorrect password
        return jsonify({"msg": "Wrong username or password"}), 401
    access_token = create_access_token(identity=user.email)
    return jsonify(access_token=access_token)
