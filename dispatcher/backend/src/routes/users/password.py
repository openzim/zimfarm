from typing import Union

from bson import ObjectId
from flask import request, Response
from werkzeug.security import check_password_hash, generate_password_hash

from routes import authenticate2, url_object_id, errors
from utils.token import AccessToken
from utils.mongo import Users


@authenticate2
@url_object_id(['user'])
def update(token: AccessToken.Payload, user: Union[ObjectId, str]):
    request_json = request.get_json()
    filter = {'$or': [{'_id': user}, {'username': user}]}
    if user == token.user_id or user == token.username:
        # user is trying to set their own password

        # get current password
        password_current = request_json.get('current', None)
        if password_current is None:
            raise errors.BadRequest()

        # get current password hash
        user = Users().find_one(filter, {'password_hash': 1})
        if user is None:
            raise errors.NotFound()

        # check current password is valid
        is_valid = check_password_hash(user['password_hash'], password_current)
        if not is_valid:
            raise errors.Unauthorized()
    else:
        # user is trying to set other user's password
        # check permission
        if not token.get_permission('users', 'reset_password'):
            raise errors.NotEnoughPrivilege()

    # get new password
    password_new = request_json.get('new', None)
    if password_new is None:
        raise errors.BadRequest()

    # set new password
    matched_count = Users().update_one(filter, {'$set': {
        'password_hash': generate_password_hash(password_new)}}).matched_count

    # send response
    if matched_count == 0:
        raise errors.NotFound()
    else:
        return Response()
