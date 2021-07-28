from datetime import datetime, timezone
from flask import jsonify, request, url_for, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity,\
     get_jwt, unset_jwt_cookies
from .. import db, bcrypt, jwt
from ..models import User, Post, Permission, BlacklistToken
from . import api
from .errors import bad_request, forbidden

# Callback function to check if a JWT exists in the database blocklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = db.session.query(BlacklistToken.id).filter_by(token=jti).scalar()
    return token is not None


@api.route('/user_account/<int:user_id>', methods=["GET"])
@jwt_required()
def get_user(user_id):
    current_user = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(logged_in_as=current_user, user=user.convert_user_json()), 200


@api.route('/users/', methods=["GET", "POST"])
@jwt_required()
def get_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_all_users')
    return jsonify(data), 200


# new user registration
@api.route('/new_user/', methods=["POST"])
def add_new_user():
    new_usr = request.get_json() or {}
    if 'username' not in new_usr or new_usr['username'] == '' or new_usr['email'] == '' or 'email' not in new_usr\
            or new_usr['password'] == '' or 'password' not in new_usr:
        return bad_request("User must have username, email and password fields. Please check your input data.")
    if User.query.filter_by(username=new_usr['username']).first():
        return bad_request("Please choose other username.")
    if User.query.filter_by(email=new_usr['email']).first():
        return bad_request("Please choose other email.")
    new_usr['password'] = bcrypt.generate_password_hash(new_usr['password']).decode('utf-8')
    user = User()
    user.convert_user_from_json(new_usr, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.convert_user_json())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', user_id=user.id)
    return response, 200


# later need to add possibility to:
# - change picture, change email, change password
@api.route('/user_account/<int:id>', methods=["PUT"])
@jwt_required()
def modify_user(id):
    user = User.query.get_or_404(id)
    if g.current_user != user and not g.current_user.can(Permission.ADMIN):
        return forbidden('You have no right to amend user info!!!')
    new_data = request.get_json() or {}
    if 'username' in new_data and new_data['username'] != user.username and\
        User.query.filter_by(username=new_data['username']).first():
        return bad_request('Please, use a different username!')
    if 'email' in new_data and new_data['email'] != user.email and\
        User.query.filter_by(username=new_data['email']).first():
        return bad_request('Please, use a different email.')
    user.convert_user_from_json(new_data, new_user=False)
    db.session.commit()
    return jsonify(user.convert_user_json()), 200


@api.route('/user/<int:id>/followers', methods=["GET"])
@jwt_required()
def get_user_followers(id):
    user = User.query.get_or_404(id)
    if not user:
        return bad_request("Some error happened while processing your request.")
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page,
                                         per_page=current_app.config['MYRECBLOG_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    prev = None
    if pagination.has_prev:
        prev = url_for('api.user_followers', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.user_followers', id=id, page=page + 1)
    return jsonify({
        'follower': [item.convert_follower_json() for item in user.followers],
        'prev_url': prev,
        'next_url': next,
        'count': pagination.total
    }), 200


@api.route('/user/<int:id>/followed', methods=["GET"])
@jwt_required()
def get_followed_users(id):
    user = User.query.get_or_404(id)
    if not user:
        return bad_request("Some error happened while processing your request.")
    page = request.args.get('page', 1, type=int )
    pagination = user.followed.paginate(page,
                                         per_page=current_app.config['MYRECBLOG_FOLLOWED_PER_PAGE'],
                                         error_out=False)
    prev = None
    if pagination.has_prev:
        prev = url_for('api.user_followed', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.user_followed', id=id, page=page + 1)
    return jsonify({
        'followed_by': [item.convert_followed_json() for item in user.followed],
        'prev_url': prev,
        'next_url': next,
        'count': pagination.total
    }), 200


@api.route('/user_posts/<int:id>', methods=['GET'])
@jwt_required()
def get_user_posts(id):
    page = request.args.get('page', 1, type=int)
    user = User.query.get_or_404(id)
    pagination = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).\
        paginate(page, per_page=current_app.config['MYRECBLOG_POSTS_PER_PAGE'],
                 error_out=False )
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', id=id, page=page + 1)
    return jsonify({'posts': [post.convert_post_json() for post in posts],
                     'prev_url': prev,
                     'next_url': next,
                     'count': pagination.total
                     }), 200


@api.route('/user_account/<int:id>/followed_posts')
@jwt_required()
def get_followed_posts(id):
    page = request.args.get('page', 1, type=int)
    user = User.query.get_or_404(id)
    pagination = user.followed_posts.order_by(Post.date_posted.desc()). \
        paginate(page, per_page=current_app.config['MYRECBLOG_POSTS_PER_PAGE'],
                  error_out=False )
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', id=id, page=page + 1)
    return jsonify({'posts': [post.convert_post_json() for post in posts],
                     'prev_url': prev,
                     'next_url': next,
                     'count': pagination.total
                     }), 200

# logout user and expire token
@api.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    token = get_jwt()["jti"]
    db.session.add(BlacklistToken(token=token))
    db.session.commit()
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    print(response.status_code)
    return response
