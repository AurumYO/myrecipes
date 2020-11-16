from flask import jsonify
from ..exceptions import ValidationError
from . import api


def bad_request(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


@api.errorhandler(ValidationError)
def validation_error(error):
    return bad_request(error.args[0])
