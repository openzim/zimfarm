from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError
from bson import ObjectId

from utils.mongo import Schedules
from utils.token import AccessToken
from . import errors


blueprint = Blueprint('schedules', __name__, url_prefix='/api/schedules')


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
            schema = {
                "type": "object",
                "properties": {
                    "offliner": {"type": "string", "enum": ["mwoffliner"]},
                    "config": {"anyOf": [
                        {"$ref": "#/definitions/mwoffliner_config"}
                    ]},
                },
                "required": ["offliner", "config"],
                "additionalProperties": False,
                "definitions": {
                    "mwoffliner_config": {
                        "type": "object",
                        "properties": {
                            "mwUrl": {"type": "string"},
                            "adminEmail": {"type": "string"}
                        },
                        "required": ["mwUrl", "adminEmail"]
                    }
                }
            }
            request_json = request.get_json()
            validate(request_json, schema)
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

    if request.method == "GET":
        schedule = Schedules().find_one({'_id': ObjectId(schedule_id)})
        if schedule is None:
            raise errors.NotFound()
        return jsonify(schedule)
    elif request.method == "PATCH":
        return Response()
    elif request.method == "DELETE":
        deleted_count = Schedules().delete_one({'_id': ObjectId(schedule_id)}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()
        return Response()
