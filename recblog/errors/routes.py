from flask import Blueprint
from flask import render_template
from recblog import db

errors = Blueprint('errors', __name__)

@errors.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@errors.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403

@errors.errorhandler(500)
def error_500(error):
    db.session.rollback()
    render_template('500.html'), 500
