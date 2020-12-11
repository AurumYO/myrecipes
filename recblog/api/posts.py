from flask import jsonify, request, url_for, g, current_app, flash
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


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def get_new_post():
    post = Post.convert_post_from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.convert_post_json()), 201, {'Location': url_for('api.get_post', post_id=post.id)}


@api.route('/posts/<int:post_id>', methods=['PUT'])
@permission_required(Permission.WRITE)
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if g.current_user != post.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permission rights. You cannot edit this post.')
    # obtain new values of the posts fields
    post.title = request.json.get('name', post.title)
    post.description = request.json.get('description', post.description)
    # in 2021 release to improve update of the new pictures instead of existing
    post.post_image = request.json.get('image', post.post_image)
    post.portions = request.json.get('portions', post.portions)
    post.recipe_yield = request.json.get('recipeYield', post.recipe_yield)
    post.cook_time = request.json.get('cookTime', post.cook_time)
    post.prep_time = request.json.get('prepTime', post.prep_time)
    post.ready = request.json.get('ready', post.ready)
    post.type_category = request.json.get('recipeCategory', post.type_category)
    post.main_ingredient = request.json.get('main_ingredient', post.main_ingredient)
    post.ingredients = request.json.get('recipeIngredient', post.ingredients)
    post.preparation = request.json.get('recipeInstructions', post.preparation)
    # save updated values of the post fields to the database
    db.session.commit()
    return jsonify(post.convert_post_json())


@api.route('/posts/<int:post_id>', methods=['DELETE'])
@permission_required(Permission.WRITE)
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if g.current_user != post.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permission rights. You cannot delete this post.')
    db.session.delete(post)
    db.session.commit()
    return jsonify({'Status': 'Post has been deleted successfully.'}), 201
