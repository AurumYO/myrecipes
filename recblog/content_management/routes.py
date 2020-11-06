from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import login_required
from flask_admin.contrib.sqla import ModelView
from .. import db, admin
from ..models import Post, Permission, User, Comment
from . import admins
from .decorators import admin_required, permission_required


## later replace with app.app_context_processor
@admins.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)


@admins.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return 'For admins only!'


admin.add_view( ModelView(User, db.session))
admin.add_view( ModelView(Post, db.session))
admin.add_view(ModelView(Comment, db.session))


@admins.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.comment_date.desc()).paginate(
        page, per_page=current_app.config['MYRECBLOG_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination, page=page)


@admins.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@admins.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))