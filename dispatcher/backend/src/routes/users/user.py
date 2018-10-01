
from flask import request, jsonify

from routes import authenticate2, errors
from utils.mongo import Users
from utils.token import AccessToken


@authenticate2
def list(token: AccessToken.Payload):
    # check user permission
    if not token.get_permission('users', 'read', False):
        raise errors.NotEnoughPrivilege()

    # unpack url parameters
    skip = request.args.get('skip', default=0, type=int)
    limit = request.args.get('limit', default=20, type=int)
    skip = 0 if skip < 0 else skip
    limit = 20 if limit <= 0 else limit

    # get users from database
    cursor = Users().find({}, {'_id': 1, 'username': 1, 'email': 1})
    users = [user for user in cursor]

    return jsonify({
        'meta': {
            'skip': skip,
            'limit': limit,
        },
        'items': users
    })
