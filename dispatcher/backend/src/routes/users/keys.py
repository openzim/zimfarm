from bson import ObjectId
from flask import Blueprint, request, jsonify, Response

from routes import authenticate, bson_object_id, errors
from utils.mongo import Users


@authenticate
@bson_object_id(['user_id'])
def list(user_id: ObjectId, user: dict):
    # TODO: check permission
    ssh_keys = Users().find_one({'_id': user_id}, {'ssh_keys': 1}).get('ssh_keys', [])
    return jsonify(ssh_keys)


@authenticate
@bson_object_id(['user_id'])
def add(user_id: ObjectId, user: dict):
    pass
