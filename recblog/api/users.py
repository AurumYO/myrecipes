from flask import jsonify, request, url_for, g, current_app
from .. import db
from ..models import User, Post, Permission
from . import api
from .errors import bad_request, forbidden


@api.route('/user_account/<int:user_id>', methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.convert_user_json())


@api.route('/users/', methods=["GET"])
def get_all_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.username.desc()).\
        paginate(page, per_page=current_app.config['MYRECBLOG_POSTS_PER_PAGE'], error_out=False)
    users = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_all_users', id=id, page=page - 1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_all_users', id=id, page=page + 1)
    return jsonify( {'posts': [user.convert_user_json() for user in users],
                     'prev_url': prev,
                     'next_url': next,
                     'count': pagination.total
                     })


# later need to add possibility to:
# - change picture, change email, change password
@api.route('user/<int:id>', methods=["PUT"])
def modify_user(id):
    user = User.query.get_or_404(id)
    if g.current_user != user and not g.current_user.can(Permission.ADMIN):
        return forbidden('You have no right to amend user info!!!')
    # user.username = request.json.get('username')
    user.location = request.json.get('location')
    user.about_me = request.json.get('about_me')
    db.session.commit()
    return jsonify(user.convert_user_json())


# NOT IMPLEMENTED YET
# @api.route('/users/', methods=["POST"])
# def add_new_user():
#     new_user = request.get_json() or {}
#     if 'username' not in new_user or 'email' not in new_user or 'password' not in new_user:
#         return bad_request("User must have username, email and password fields. Please check your input data.")
#     if User.query.filter_by(username=new_user['username']).first():
#         return bad_request("Please choose other username.")
#     if User.query.filter_by(email=new_user['email']).first():
#         return bad_request("Please choose other email.")
#     user = User()
#     user = user.convert_user_from_json(new_user)
#     db.session.add(user)
#     db.session.commit()
#     return jsonify(user.convert_user_json()), 201, {'Location': url_for('api.get_user', id=user.id)}


@api.route('/user/<int:id>/followers', methods=["GET"])
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
    })


@api.route('/user/<int:id>/followed', methods=["GET"])
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
    })


@api.route('/user_posts/<int:id>', methods=['GET'])
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
                     })


@api.route('/user_account/<int:id>/followed_posts')
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
                     })
