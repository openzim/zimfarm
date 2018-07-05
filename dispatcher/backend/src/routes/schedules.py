from celery.schedules import crontab
from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError
from pymongo.errors import DuplicateKeyError

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

    offliner = {
        "oneOf": [{
            "type": "object",
            "properties": {
                "name": {"type": "string", "enum": ["mwoffliner"]},
                "config": {
                    "type": "object",
                    "properties": {
                        "mwUrl": {"type": "string"},
                        "adminEmail": {"type": "string"},
                    },
                    "additionalProperties": False
                }
            },
            "required": ["name", "config"],
            "additionalProperties": False
        }]
    }

    task = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": ["mwoffliner"]},
        },
        "required": ["name"],
        "additionalProperties": False
    }

    create = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["wikipedia"]},
            "enabled": {"type": "boolean"},
            "language": {"type": "string"},
            "name": {"type": "string"},
            "queue": {"type": "string", "enum": ["tiny", "small", "medium", "large"]},
            "beat": beat,
            "offliner": offliner,
            "task": task
        },
        "required": ["category", "enabled", "language", "name", "queue", "beat", "offliner", "task"],
        "additionalProperties": False
    }


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
            'queue': 1,
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
            validate(request_json, Schema.create)
        except ValidationError as error:
            raise errors.BadRequest(error.message)

        # insert document into database
        try:
            schedule_id = Schedules().insert_one(request_json).inserted_id
            return jsonify({'_id': schedule_id})
        except DuplicateKeyError:
            raise errors.BadRequest('name {} already exists'.format(request_json['name']))


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
    elif request.method == "PATCH":
        # check user permission
        if not user.get('scope', {}).get('schedules', {}).get('update', False):
            raise errors.NotEnoughPrivilege()

    elif request.method == "DELETE":
        # check user permission
        if not user.get('scope', {}).get('schedules', {}).get('delete', False):
            raise errors.NotEnoughPrivilege()

        deleted_count = Schedules().delete_one({'name': name}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()
        return Response()


@blueprint.route("/<string:name>/beat", methods=["PATCH"])
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

        # test crontab
        try:
            config = request_json['config']
            crontab(minute=config.get('minute', '*'),
                    hour=config.get('hour', '*'),
                    day_of_week=config.get('day_of_week', '*'),
                    day_of_month=config.get('day_of_month', '*'),
                    month_of_year=config.get('month_of_year', '*'))
        except Exception:
            raise errors.BadRequest()

        # update database
        matched_count = Schedules().update_one({'name': name}, {'$set': {'beat': request_json}}).matched_count
        if matched_count == 0:
            raise errors.NotFound()
        return jsonify({'name': name})


@blueprint.route("/<string:name>/<string:property_name>", methods=["GET", "PATCH"])
@authenticate
def schedule_offliner(name: str, property_name: str, user: dict):
    """
    Get or Update beat, offliner or task of one schedule
    """
    if property_name not in ['offliner', 'task']:
        raise errors.NotFound()

    if request.method == "GET":
        schedule = Schedules().find_one({'name': name}, {property_name: 1})
        if schedule is None:
            raise errors.NotFound()
        return jsonify(schedule[property_name])
    elif request.method == "PATCH":
        # check user permission
        if not user.get('scope', {}).get('schedules', {}).get('update', False):
            raise errors.NotEnoughPrivilege()

        # validate request json
        request_json = request.get_json()
        if property_name == 'offliner':
            schema = Schema.offliner
        elif property_name == 'task':
            schema = Schema.task
        else:
            schema = None
        try:
            validate(request_json, schema)
        except ValidationError as error:
            raise errors.BadRequest(error.message)

        # update database
        matched_count = Schedules().update_one({'name': name}, {'$set': {'property_name': request_json}}).matched_count
        if matched_count == 0:
            raise errors.NotFound()
        return jsonify({'name': name})
