from flask import g, request, jsonify
from flask_jwt_extended import create_access_token
from recblog.models import User
from . import api
from recblog.api.errors import unauthorized, forbidden

# login user with JWT-token
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

# # Using an `after_request` callback, we refresh any token that is within 30
# # minutes of expiring. Change the timedeltas to match the needs of your application.
# @app.after_request
# def refresh_expiring_jwts(response):
#     try:
#         exp_timestamp = get_jwt()["exp"]
#         now = datetime.now(timezone.utc)
#         target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
#         if target_timestamp > exp_timestamp:
#             access_token = create_access_token(identity=get_jwt_identity())
#             set_access_cookies(response, access_token)
#         return response
#     except (RuntimeError, KeyError):
#         # Case where there is not a valid JWT. Just return the original respone
#         return response


