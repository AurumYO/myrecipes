from flask import render_template, request, jsonify
from . import errors
from .. import db


@errors.errorhandler(404)
def error_404(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@errors.errorhandler(403)
def error_403(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403


@errors.errorhandler(500)
def error_500(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 500
        return response
    db.session.rollback()
    render_template('500.html'), 500
