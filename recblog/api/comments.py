from flask import jsonify, request, current_app, url_for, g
from .. import db
from . import api
from ..models import Permission, Post, Comment
from .utils import permission_required
from .errors import forbidden


@api.route('/comments/')
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
def get_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return jsonify(comment.convert_comment_to_json())


@api.route('/post/<int:post_id>/comments/')
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


@api.route('/post/<int:post_id>/comments', methods=["POST"])
@permission_required(Permission.WRITE)
@permission_required(Permission.COMMENT)
def new_comment_to_post(post_id):
    post = Post.query.get_or_404(post_id)
    comment = Comment.convert_from_json_comment(request.json)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.convert_comment_to_json()), 201,\
           {'Location': url_for('api.get_comment', comment_id=comment.id)}


@api.route('/comments/<int:comment_id>', methods=['PUT'])
@permission_required(Permission.WRITE)
@permission_required(Permission.COMMENT)
def update_comment_to_post(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if g.current_user != comment.author and not g.current_user.can(Permission.MODERATE)\
            or g.current_user != comment.author and not g.current_user.can(Permission.ADMIN):
        return forbidden("You have no permission to change this comment!")
    comment.body = request.json.get('body')
    db.session.commit()
    return jsonify(comment.convert_comment_to_json())


@api.route('/comments/<int:comment_id>', methods=["DELETE"])
@permission_required(Permission.WRITE)
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if g.current_user != comment.author and not g.current_user.can(Permission.MODERATE)\
            or g.current_user != comment.author and not g.current_user.can(Permission.ADMIN):
        return forbidden('You have no permission  to delete the comment!')
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'Status: ': 'Comment was successfully deleted'})
