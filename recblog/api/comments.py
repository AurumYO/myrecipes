from flask import jsonify, request, current_app, url_for, g
from .. import db
from . import api
from ..models import Permission, Post, Comment
from .utils import permission_required


# @api.route('/comments/')
# def get_all_comments():
#     page = request.args.get('page', 1, type=int)
#     pagination = Comment.query.order_by(Comment.comment_date.desc())\
#         .paginate(page, per_page=current_app.config['MYRECBLOG_COMMENTS_PER_PAGE'], error_out=False)
#     all_comments = pagination.items
#     prev = None
#     if all_comments.has_prev:
#         prev = url_for('api.get_all_comments', id=id, page=page-1)
#     next = None
#     if all_comments.has_next:
#         next = url_for('api.get_all_comments', id=id, page=page+1)
#     return jsonify({
#         'comment': [comment.convert_comment_to_json() for comment in all_comments],
#         'prev': prev,
#         'next': next,
#         'count': pagination.total
#     })


# @api.route('/comments/<int:id>')
# def get_comment(id):
#     comment = Comment.query.get_or_404(id)
#     return jsonify(comment.convert_comment_to_json())

#
# @api.route('/posts/<int:id>/comments')
# def get_post_comments(id):
#     page = request.args.get('page', 1, type=int)
#     pagination = Comment.query.paginate(page, per_page=current_app.config['MYRECBLOG_COMMENTS_PER_PAGE'],
#                                         error_out=False)
#     post_comments = pagination.items
#     prev = None
#     if post_comments.has_prev:
#         prev = url_for('api.get_post_comments', id=id, page=page-1)
#     next = None
#     if post_comments.has_next:
#         next = url_for('api.get_post_comments', id=id, page=page+1)
#
#     return jsonify({
#         'comments': [comment.convert_comment_to_json() for comment in post_comments],
#         'prev': prev,
#         'next': next,
#         'count': pagination.total
#     })
#
#
# @api.route('/post/<int:post_id>/comments', methods=["POST"])
# @permission_required(Permission.WRITE)
# def new_comment_to_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     comment = Comment.convert_from_json_comment(request.json)
#     comment.author = g.current_user
#     comment.post = post
#     db.session.add(comment)
#     db.session.commit()
#     return jsonify(comment.convert_comment_to_json()), 201, {'Location': url_for('api.get_comment', id=comment.id)}
