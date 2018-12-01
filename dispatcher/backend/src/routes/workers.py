from bson import ObjectId
from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError
from celery.app.control import Inspect

from app import celery
from utils.mongo import Workers
from . import authenticate2, bson_object_id, errors

from utils.token import AccessToken


blueprint = Blueprint('workers', __name__, url_prefix='/api/workers')


@blueprint.route("/", methods=["GET"])
@authenticate2
def list_workers(token: AccessToken.Payload):
    workers = Workers()
    workers = [workers for workers in workers.find({}, {'_id': 1, 'hostname': 1, 'status': 1, 'session': 1})]
    return jsonify(workers)
