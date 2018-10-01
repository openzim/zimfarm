from functools import wraps

import flask
# from bson.objectid import ObjectId, InvalidId
# from flask import Blueprint, request, jsonify, Response
# from jsonschema import validate, ValidationError
# from werkzeug.security import check_password_hash, generate_password_hash

from . import user, keys
# from .. import authenticate, bson_object_id, errors
# from utils.mongo import Users


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('users', __name__, url_prefix='/api/users')
        self.add_url_rule('/', 'list_users', user.list, methods=['GET'])
