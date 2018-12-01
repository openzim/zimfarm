from bson import ObjectId
from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError
from celery.app.control import Inspect

from app import celery
from utils.mongo import Schedules
from . import authenticate2, bson_object_id, errors

from utils.token import AccessToken


blueprint = Blueprint('workers', __name__, url_prefix='/api/workers')


@blueprint.route("/", methods=["GET"])
@authenticate2
def list_workers(token: AccessToken.Payload):
    inspect: Inspect = celery.control.inspect()
    return jsonify(inspect.ping())