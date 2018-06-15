from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from bson import ObjectId

from utils.mongo import Schedules
from utils.token import AccessToken
from . import errors


blueprint = Blueprint('schedules', __name__, url_prefix='/api/schedules')


@blueprint.route("/", methods=["GET", "POST"])
def schedules():
    if request.method == "GET":
        # check token exist and is valid
        token = AccessToken.decode(request.headers.get('token'))
        if token is None:
            raise errors.Unauthorized()

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

        # send the response
        return jsonify({
            'meta': {
                'skip': skip,
                'limit': limit,
            },
            'items': schedules
        })
    elif request.method == "POST":
        pass