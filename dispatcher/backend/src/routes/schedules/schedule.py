from celery.schedules import crontab
from flask import Blueprint, request, jsonify, Response
from jsonschema import validate, ValidationError
from pymongo.errors import DuplicateKeyError

from mongo import Schedules
from utils.token import AccessControl
from .. import auth, errors


@auth
def list(token: AccessControl):
    """Return a list of schedules"""

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
