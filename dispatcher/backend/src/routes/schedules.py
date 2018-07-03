from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError

from utils.mongo import Schedules
from . import authenticate, errors


blueprint = Blueprint('schedules', __name__, url_prefix='/api/schedules')


class Schema:
    beat = {
        "oneOf": [{
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["crontab"]},
                "config": {
                    "type": "object",
                    "properties": {
                        "minute": {"type": ["string", "number"]},
                        "hour": {"type": ["string", "number"]},
                        "day_of_week": {"type": ["string", "number"]},
                        "day_of_month": {"type": ["string", "number"]},
                        "month_of_year": {"type": ["string", "number"]},
                    },
                    "additionalProperties": False
                }
            },
            "required": ["type", "config"],
            "additionalProperties": False
        }]
    }

    @staticmethod
    def mwoffliner_config(check_required: bool=True) -> dict:
        schema = {
            "type": "object",
            "properties": {
                "mwUrl": {"type": "string"},
                "adminEmail": {"type": "string"}
            }
        }
        if check_required:
            schema["required"] = ["mwUrl", "adminEmail"]
        return schema

    @staticmethod
    def document(check_required: bool=True) -> dict:
        task_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "config": {"anyOf": [
                    Schema.mwoffliner_config(check_required)
                ]}
            },
            "required": ["name", "config"]
        }
        schema = {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["wikipedia"]},
                "language": {"type": "string"},
                "offliner": {"type": "string", "enum": ["mwoffliner"]},
                "task": task_schema,
                "beat": Schema.beat
            },
            "required": ["category", "language", "offliner", "task", "beat"],
            "additionalProperties": False
        }
        return schema


@blueprint.route("/", methods=["GET", "POST"])
@authenticate
def collection(user: dict):
    """
    List or Create schedules
    """
    if request.method == "GET":
        # unpack url parameters
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=20, type=int)
        skip = 0 if skip < 0 else skip
        limit = 20 if limit <= 0 else limit

        # get schedules from database
        projection = {
            '_id': 0,
            'beat': 1,
            'category': 1,
            'enabled': 1,
            'language': 1,
            'last_run': 1,
            'name': 1,
            'total_run': 1
        }
        cursor = Schedules().find({}, projection).skip(skip).limit(limit)
        schedules = [schedule for schedule in cursor]

        return jsonify({
            'meta': {
                'skip': skip,
                'limit': limit,
            },
            'items': schedules
        })
    elif request.method == "POST":
        # check user permission
        if not user.get('scope', {}).get('schedules', {}).get('create', False):
            raise errors.NotEnoughPrivilege()

        # validate request json
        try:
            request_json = request.get_json()
            validate(request_json, Schema.document())
        except ValidationError as error:
            raise errors.BadRequest(error.message)

        schedule_id = Schedules().insert_one(request_json).inserted_id
        return jsonify({'_id': schedule_id})


@blueprint.route("/<string:name>", methods=["GET", "PATCH", "DELETE"])
@authenticate
def document(name: str, user: dict):
    """
    Get or Delete one schedule
    # TODO: Update top level properties of one schedule
    """
    if request.method == "GET":
        schedule = Schedules().find_one({'name': name})
        if schedule is None:
            raise errors.NotFound()
        return jsonify(schedule)
    elif request.method == "DELETE":
        # check user permission
        if not user.get('scope', {}).get('schedules', {}).get('delete', False):
            raise errors.NotEnoughPrivilege()

        deleted_count = Schedules().delete_one({'name': name}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()
        return Response()


@blueprint.route("/<string:name>/beat", methods=["GET", "PATCH"])
@authenticate
def schedule_beat(name: str, user: dict):
    """
    Get or Update beat of one schedule
    """
    if request.method == "GET":
        schedule = Schedules().find_one({'name': name}, {'beat': 1})
        if schedule is None:
            raise errors.NotFound()
        return jsonify(schedule['beat'])
    elif request.method == "PATCH":
        # check user permission
        if not user.get('scope', {}).get('schedules', {}).get('update', False):
            raise errors.NotEnoughPrivilege()

        # validate request json
        request_json = request.get_json()
        try:
            validate(request_json, Schema.beat)
        except ValidationError as error:
            raise errors.BadRequest(error.message)

        # update database
        matched_count = Schedules().update_one({'name': name}, {'$set': {'beat': request_json}}).matched_count
        if matched_count == 0:
            raise errors.NotFound()
        return jsonify({'name': name})


# @blueprint.route("/<string:schedule_id>/task/config", methods=["PATCH"])
# @authenticate
# @bson_object_id(['schedule_id'])
# def config(schedule_id: ObjectId, user: dict):
#     # check user permission
#     if not user.get('scope', {}).get('schedules', {}).get('update_task_config', False):
#         raise errors.NotEnoughPrivilege()
#
#     # validate request json
#     try:
#         request_json = request.get_json()
#         # TODO: add capabilities to validate other offliner config
#         validate(request_json, Schema.mwoffliner_config(check_required=False))
#     except ValidationError as error:
#         raise errors.BadRequest(error.message)
#
#     task_config = Schedules().find_one({'_id': schedule_id}, {'task.config': 1})['task']['config']
#     for key, value in request_json.items():
#         task_config[key] = value
#     Schedules().update_one({'_id': schedule_id}, {'$set': {'task.config': task_config}})
#     return jsonify({'_id': schedule_id})
