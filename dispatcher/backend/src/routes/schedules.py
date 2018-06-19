from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError

from utils.mongo import Schedules
from . import authenticate, bson_object_id, errors


blueprint = Blueprint('schedules', __name__, url_prefix='/api/schedules')


class Schema:
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
    def schedule() -> dict:
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["crontab"]},
                "config": {"type": "object"}
            },
            "required": ["type", "config"]
        }

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
                "category": {"type": "string"},
                "language": {"type": "string"},
                "offliner": {"type": "string", "enum": ["mwoffliner"]},
                "task": task_schema,
                "schedule": Schema.schedule()
            },
            "required": ["category", "language", "offliner", "task", "schedule"],
            "additionalProperties": False
        }
        return schema


@blueprint.route("/", methods=["GET", "POST"])
@authenticate
def collection(user: dict):
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
        # check user permission
        if not user.get('scope', {}).get('schedule', {}).get('create', False):
            raise errors.NotEnoughPrivilege()

        # validate request json
        try:
            request_json = request.get_json()
            validate(request_json, Schema.document())
        except ValidationError as error:
            raise errors.BadRequest(error.message)

        schedule_id = Schedules().insert_one(request_json).inserted_id
        return jsonify({'_id': schedule_id})


@blueprint.route("/<string:schedule_id>", methods=["GET", "PATCH", "DELETE"])
@authenticate
@bson_object_id(['schedule_id'])
def document(schedule_id, user):
    if request.method == "GET":
        schedule = Schedules().find_one({'_id': schedule_id})
        if schedule is None:
            raise errors.NotFound()
        return jsonify(schedule)
    elif request.method == "DELETE":
        # check user permission
        if not user.get('scope', {}).get('schedule', {}).get('delete', False):
            raise errors.NotEnoughPrivilege()

        deleted_count = Schedules().delete_one({'_id': schedule_id}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()
        return Response()


@blueprint.route("/<string:schedule_id>/task/config", methods=["PATCH"])
@authenticate
@bson_object_id(['schedule_id'])
def config(schedule_id, user):
    # check user permission
    if not user.get('scope', {}).get('schedule', {}).get('update_task_config', False):
        raise errors.NotEnoughPrivilege()

    # validate request json
    try:
        request_json = request.get_json()
        # TODO: add capabilities to validate other offliner config
        validate(request_json, Schema.mwoffliner_config(check_required=False))
    except ValidationError as error:
        raise errors.BadRequest(error.message)

    Schedules().update_one({'_id': schedule_id}, {'$set': {'task.config': request_json}})
    return jsonify({'_id': schedule_id})
