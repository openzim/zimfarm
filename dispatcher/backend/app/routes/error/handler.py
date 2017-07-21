from flask import Response, jsonify
from . import exception


# 400
def invalid_request(_):
    return Response(status=400)

def username_not_valid(_):
    response = jsonify({'error': 'username not valid'})
    response.status_code = 400
    return response

def scope_not_valid(_):
    response = jsonify({'error': 'scope not valid'})
    response.status_code = 400
    return response

# 401
def jwt_decode_error(_):
    response = jsonify({'error': 'token invalid'})
    response.status_code = 401
    return response

def jwt_expired(_):
    response = jsonify({'error': 'token expired'})
    response.status_code = 401
    return response

def not_enough_privilege(_):
    response = jsonify({'error': 'you are not authorized to perform this operation'})
    response.status_code = 401
    return response

def auth_failed(_):
    response = jsonify({'error': 'username or password invalid'})
    response.status_code = 401
    return response

# 404
def user_does_not_exist(_):
    response = jsonify({'error': 'user does not exist'})
    response.status_code = 404
    return response

def task_does_not_exist(_):
    response = jsonify({'error': 'task does not exist'})
    response.status_code = 404
    return response

# 409
def user_already_exists(_):
    response = jsonify({'error': 'user already exists'})
    response.status_code = 409
    return response

#500
def rabbitmq_error(error: exception.RabbitMQError):
    response = jsonify({'error': 'RabbitMQ Error: code({})'.format(error.code)})
    response.status_code = 500
    return response

def rabbitmq_put_user_failed(error: exception.RabbitMQPutUserFailed):
    response = jsonify({'error': 'RabbitMQ Error: add user failed, code({})'.format(error.code)})
    response.status_code = 500
    return response

def rabbitmq_put_permission_failed(error: exception.RabbitMQPutPermissionFailed):
    response = jsonify({'error': 'RabbitMQ Error: set permission failed, code({})'.format(error.code)})
    response.status_code = 500
    return response

def rabbitmq_delete_user_failed(error: exception.RabbitMQDeleteUserFailed):
    response = jsonify({'error': 'RabbitMQ Error: delete user failed, code({})'.format(error.code)})
    response.status_code = 500
    return response