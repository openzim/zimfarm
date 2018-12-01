from flask import jsonify

from utils.mongo import Workers
from utils.token import AccessToken


def list(token: AccessToken.Payload):
    workers = Workers()
    workers = [workers for workers in workers.find({}, {'_id': 1, 'hostname': 1, 'status': 1, 'session': 1})]
    return jsonify(workers)