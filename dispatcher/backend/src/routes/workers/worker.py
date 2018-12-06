from flask import jsonify

from utils.mongo import Workers
from utils.token import AccessToken

from .. import authenticate2


@authenticate2
def list():
    projection = {
        '_id': 1,
        'hostname': 1,
        'status': 1,
        'session': 1,
        # 'heartbeats': {'$slice': -1},
        # 'load_average.1_min': {'$slice': -1},
        # 'load_average.5_mins': {'$slice': -1},
        # 'load_average.15_mins': {'$slice': -1},
    }
    workers = Workers()
    workers = [workers for workers in workers.find({}, projection)]
    return jsonify(workers)