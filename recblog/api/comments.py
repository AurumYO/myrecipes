from flask import jsonify, request, current_app, url_for, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from . import api
from ..models import Permission, Post, Comment, User
from .utils import permission_required
from .errors import forbidden, bad_request


@api.route('/comments/')
@jwt_required()
def get_all_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.comment_date.desc())\
        .paginate(page, per_page=current_app.config['MYRECBLOG_COMMENTS_PER_PAGE'], error_out=False)
    all_comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_all_comments', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_all_comments', page=page+1)
    return jsonify({
        'comment': [comment.convert_comment_to_json() for comment in all_comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/comment/<int:comment_id>')
@jwt_required()
def get_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return jsonify(comment.convert_comment_to_json())


@api.route('/post/<int:post_id>/comments/')
@jwt_required()
def get_post_comment(post_id):
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.filter_by(post_id=post_id).order_by(Comment.comment_date.asc()).\
        paginate(page, per_page=current_app.config['MYRECBLOG_COMMENTS_PER_PAGE'], error_out=False )
    all_comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_post_comment', page=page - 1 )
    next = None
    if pagination.has_next:
        next = url_for('api.get_post_comment', page=page + 1 )
    return jsonify({
        'comment': [comment.convert_comment_to_json() for comment in all_comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/post/<int:post_id>/comments/', methods=["POST"])
@jwt_required()
@permission_required(Permission.WRITE)
@permission_required(Permission.COMMENT)
def new_comment_to_post(post_id):
    new_comment = request.get_json() or {}
    new_comment['author_id'] = User.query.filter_by(email=get_jwt_identity()).first().id
    comment = Comment()
    comment.convert_from_json_comment(new_comment)
    db.session.add(comment)
    db.session.commit()
    response = jsonify(comment.convert_comment_to_json())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_comment', comment_id=comment.id)
    return response, 201


@api.route('/comment/<int:comment_id>', methods=['PUT'])
@jwt_required()
@permission_required(Permission.WRITE)
@permission_required(Permission.COMMENT)
def update_comment(comment_id):
    updated_comment = request.get_json() or {}
    comment = Comment.query.filter_by(id=comment_id).first()
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    print(comment.author, current_user)
    if current_user != comment.author and not current_user.can(Permission.MODERATE)\
            or current_user != comment.author and not current_user.can(Permission.ADMIN):
        return forbidden("You have no permission to change this comment!")
    comment.body = updated_comment['body']
    db.session.commit()
    return jsonify(comment.convert_comment_to_json()), 200


@api.route('/comment/<int:comment_id>', methods=["DELETE"])
@jwt_required()
@permission_required(Permission.WRITE)
@permission_required(Permission.COMMENT)
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    current_user = User.query.filter_by(email=get_jwt_identity()).first()
    if current_user != comment.author and not current_user.can(Permission.MODERATE)\
            or current_user != comment.author and not current_user.can(Permission.ADMIN):
        return forbidden('You have no permission to delete the comment!')
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'Status: ': 'Comment was successfully deleted'}), 200
