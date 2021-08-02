from flask import jsonify, request, url_for, g, current_app, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
import ast
from .. import db
from ..models import User, Post, Permission, FavoritePosts
from . import api
from .utils import permission_required
from .errors import bad_request, forbidden


@api.route('/posts/')
@jwt_required()
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
@jwt_required()
@permission_required(Permission.WRITE)
def get_post(post_id):
    user = User.query.filter_by(email=get_jwt_identity()).first()
    post = Post.query.get_or_404(post_id)
    return jsonify(post.convert_post_json()), 200


@api.route('/post_new/', methods=['POST'])
@jwt_required()
@permission_required(Permission.WRITE)
def get_new_post():
    new_post = request.get_data()
    new_post = ast.literal_eval(new_post.decode("UTF-8"))
    # perform check if post has all obligatory fields
    required_fileds = ['name', 'description', 'portions', 'cookTime', 'recipeCategory',\
                           'recipeIngredient', 'recipeInstructions']
    # check if some required filelds datais missing, report on missing data
    missing_parametrs = []
    for k in required_fileds:
        if k not in set(new_post.keys()):
            missing_parametrs.append(k)
    if len(missing_parametrs) > 0:
        output_params = ' '.join(str(x + ', ') for x in missing_parametrs)
        return bad_request("Post must have following parameters: {} please check your input data.".format(output_params))
    # check compleated, all is fine save the post
    post = Post()
    post = Post.convert_post_from_json(new_post)
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    post.author = current_user
    db.session.add(post)
    db.session.commit()
    response = jsonify(post.convert_post_json())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', post_id=post.id)
    return response


@api.route('/post/<int:post_id>', methods=['PUT'])
@jwt_required()
@permission_required(Permission.WRITE)
def update_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    new_post_data = request.get_data()
    new_post_data = ast.literal_eval(new_post_data.decode("UTF-8"))
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    if current_user != post.author or not current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permission rights. You cannot edit this post.')
    # obtain new values of the posts fields
    # !!TODO: optimize new values assigning
    post.title = new_post_data['name'] if new_post_data['name'] else post.title
    post.description = new_post_data['description'] if new_post_data['name'] else post.description
    # in 2021 release to improve update of the new pictures instead of existing
    post.post_image = new_post_data['image'] if new_post_data['image'] else post.post_image
    post.portions = new_post_data['portions'] if new_post_data['portions'] else post.portions
    post.recipe_yield = new_post_data['recipeYield'] if new_post_data['recipeYield'] else post.recipe_yield
    post.cook_time = new_post_data['cookTime'] if new_post_data['cookTime']  else post.cook_time
    post.prep_time = new_post_data['prepTime'] if new_post_data['prepTime'] else post.prep_time
    post.ready = new_post_data['ready'] if new_post_data['ready'] else post.ready
    post.type_category = new_post_data['recipeCategory'] if new_post_data['recipeCategory'] else post.type_category
    post.main_ingredient = new_post_data['main_ingredient'] if new_post_data['main_ingredient'] else post.main_ingredient
    post.ingredients = new_post_data['recipeIngredient'] if new_post_data['recipeIngredient'] else post.main_ingredient
    post.preparation = new_post_data['recipeInstructions'] if new_post_data['recipeInstructions'] else post.preparation
    # save updated values of the post fields to the database
    db.session.commit()
    # return updated post
    response = jsonify(post.convert_post_json())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', post_id=post.id)
    return response


@api.route('/post/<int:post_id>', methods=['DELETE'])
@jwt_required()
@permission_required(Permission.WRITE)
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    if current_user != post.author or not current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permission rights. You cannot edit this post.')
    db.session.delete(post)
    db.session.commit()
    return jsonify({'Status': 'Post has been deleted successfully.'}), 201


# like the post
@api.route('/post/<int:post_id>/like', methods=['PUT'])
@jwt_required()
def add_post_to_favorite(post_id):
    post = Post.query.filter_by(id=post_id).first()
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    if not post:
        return bad_request("Sorry, no such post!")
    if FavoritePosts.query.filter_by(post_id=post.id, liker_id=current_user.id):
        return bad_request("You already liked this post!")
    favorite = FavoritePosts(current_user.id, post.id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({
                    'msg': 'Successfully added to favorites',
                    'details': favorite.convert_favorites_json()
                }), 200


# unlike the post
@api.route('/post/<int:post_id>/unlike', methods=['DELETE'])
@jwt_required()
def unlike_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    if not post:
        return bad_request("Sorry, no such post!")
    favorite = FavoritePosts.query.filter_by(post_id=post.id, liker_id=current_user.id)
    if favorite:
        return bad_request("You have not liked this post before to unlike!")
    post.delete_post_from_favorites(current_user.id)
    db.session.commit()
    return jsonify({
                    'msg': 'Successfully unliked the post!'
                }), 200
