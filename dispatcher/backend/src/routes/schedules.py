from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError
from bson.objectid import ObjectId, InvalidId

from utils.mongo import Schedules
from utils.token import AccessToken
from . import errors


blueprint = Blueprint('schedules', __name__, url_prefix='/api/schedules')

mwoffliner_config_schema = {
    "type": "object",
    "properties": {
        "mwUrl": {"type": "string"},
        "adminEmail": {"type": "string"}
    },
    "required": ["mwUrl", "adminEmail"]
}

schedule_schema = {
    "type": "object",
    "properties": {
        "domain": {"type": "string"},
        "offliner": {"type": "string", "enum": ["mwoffliner"]},
        "config": {"anyOf": [
            {"$ref": "#/definitions/mwoffliner_config"}
        ]},
    },
    "required": ["offliner", "config"],
    "additionalProperties": False,
    "definitions": {
        "mwoffliner_config": mwoffliner_config_schema
    }
}


@blueprint.route("/", methods=["GET", "POST"])
def collection():
    # check token exist and is valid
    token = AccessToken.decode(request.headers.get('token'))
    if token is None:
        raise errors.Unauthorized()

    if request.method == "GET":
        # unpack url parameters
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=20, type=int)
        skip = 0 if skip < 0 else skip
        limit = 20 if limit <= 0 else limit

        # get schedules from database
        cursor = Schedules().aggregate([
            {'$skip': skip},
            {'$limit': limit},
        ])
        schedules = [schedule for schedule in cursor]

        return jsonify({
            'meta': {
                'skip': skip,
                'limit': limit,
            },
            'items': schedules
        })
    elif request.method == "POST":
        # validate request json
        try:
            request_json = request.get_json()
            validate(request_json, schedule_schema)
        except ValidationError as error:
            raise errors.BadRequest(error.message)

        schedule_id = Schedules().insert_one(request_json).inserted_id
        return jsonify({'_id': schedule_id})


@blueprint.route("/<string:schedule_id>", methods=["GET", "PATCH", "DELETE"])
def document(schedule_id):
    # check token exist and is valid
    token = AccessToken.decode(request.headers.get('token'))
    if token is None:
        raise errors.Unauthorized()

    # check if schedule_id is valid `ObjectID`
    try:
        schedule_id = ObjectId(schedule_id)
    except InvalidId:
        raise errors.BadRequest(message="Invalid ObjectID")

    if request.method == "GET":
        schedule = Schedules().find_one({'_id': ObjectId(schedule_id)})
        if schedule is None:
            raise errors.NotFound()
        return jsonify(schedule)
    elif request.method == "DELETE":
        deleted_count = Schedules().delete_one({'_id': ObjectId(schedule_id)}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()
        return Response()


def extract_access_token(f):
    def wrapper(*args, **kwargs):
        # check token exist and is valid
        token = AccessToken.decode(request.headers.get('token'))
        if token is None:
            raise errors.Unauthorized()

        return f(access_token=token, *args, **kwargs)
    return wrapper


@blueprint.route("/<string:schedule_id>/config", methods=["PATCH"])
@extract_access_token
def config(schedule_id, access_token):
    print(access_token)
    # check if schedule_id is valid `ObjectID`
    try:
        schedule_id = ObjectId(schedule_id)
    except InvalidId:
        raise errors.BadRequest(message="Invalid ObjectID")

    # validate request json
    try:
        request_json = request.get_json()
        # TODO: add capabilities to validate other offliner config
        validate(request_json, mwoffliner_config_schema)
    except ValidationError as error:
        raise errors.BadRequest(error.message)

    Schedules().update_one({'_id': ObjectId(schedule_id)}, {'$set': {'config': request_json}})
    return Response()
