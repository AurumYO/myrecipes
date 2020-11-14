from flask import jsonify, request, url_for, g, current_app, flash
from flask_login import login_required
from .. import db
from ..models import User, Post, Permission
from . import api
from .utils import permission_required
from .errors import forbidden


@api.route('/posts/')
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.date_posted.desc()).\
        paginate(page, per_page=current_app.config['MYRECBLOG_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', id=id, page=page+1)
    return jsonify({'posts': [post.convert_post_json() for post in posts],
                    'prev_url': prev,
                    'next_url': next,
                    'count': pagination.total
                    })


@api.route('/post/<int:post_id>')
@permission_required(Permission.WRITE)
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.convert_post_json())


# @api.route('/posts/', methods=['POST'])
# @permission_required(Permission.WRITE)
# def get_new_post():
#     post = Post.convert_post_from_json(request.json)
#     post.author = g.current_user
#     db.session.add(post)
#     db.session.commit()
#     return jsonify(post.convert_post_json()), 201, {'Location' : url_for('api.get_post', id=post.id)}


# @api.route('/posts/<int:post_id>', methods=['PUT'])
# @permission_required(Permission.WRITE)
# def update_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     if g.current_user != post.author and not g.current_user.can(Permission.ADMIN):
#         return forbidden('Insufficient permission rights. You cannot edit this post.')
#
#     post.title = request.json.get('title', post.title)
#     post.description = request.json.get('description', post.description)
#     post.post_image = request.json.get('post_image', post.post_image)
#     post.portions = request.json.get('portions', post.portions)
#     post.prep_time = request.json.get('prep_time', post.prep_time)
#     post.type_category = request.json.get('type_category', post.type_category)
#     post.ingredients = request.json.get('ingredients', post.ingredients)
#     post.preparation = request.json.get('preparation', post.preparation)
#
#     # db.session.add() is optional according to documentation once data in database
#     # delete after testing
#     db.session.add(post)
#     db.sission.commit()
#     return jsonify(post.convert_post_json())


@api.route('/posts/<int:post_id>/delete', methods=['PUT'])
@permission_required(Permission.WRITE)
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if g.current_user != post.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permission rights. You cannot delete this post.')
    db.session.delete( post )
    db.session.commit()
    return 201, 'Success'


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


