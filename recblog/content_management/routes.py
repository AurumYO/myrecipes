from flask import Blueprint
from recblog import db, admin
from recblog.models import Post, Permission, User
from flask_login import login_required
from flask_admin.contrib.sqla import ModelView
from recblog.content_management.decorators import admin_required, permission_required

admins = Blueprint('admins', __name__)

## later replace with app.app_context_processor
@admins.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Post, db.session))


@admins.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return "For admins only!"


@admins.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderators_only():
    return "For comments moderators!"
