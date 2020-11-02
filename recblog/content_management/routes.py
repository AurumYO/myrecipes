from flask import Blueprint
from flask_login import login_required
from flask_admin.contrib.sqla import ModelView
from .. import db, admin
from ..models import Post, Permission, User
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


@admins.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderators_only():
    return "For comments moderators!"


admin.add_view( ModelView(User, db.session))
admin.add_view( ModelView(Post, db.session))