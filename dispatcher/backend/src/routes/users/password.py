from http import HTTPStatus

from flask import request, Response
from werkzeug.security import check_password_hash, generate_password_hash

from routes.base import BaseRoute
from routes import authenticate, url_object_id, errors
from utils.token import AccessToken
from common.mongo import Users


class PasswordRoute(BaseRoute):
    rule = "/<string:username>/password"
    name = "password"
    methods = ["PATCH"]

    @authenticate
    @url_object_id(["username"])
    def patch(self, username: str, token: AccessToken.Payload):
        query = {"username": username}
        request_json = request.get_json()
        if username == token.username:
            # user is trying to set their own password

            # get current password
            password_current = request_json.get("current", None)
            if password_current is None:
                raise errors.BadRequest()

            # get current password hash
            user = Users().find_one(query, {"password_hash": 1})
            if user is None:
                raise errors.NotFound()

            # check current password is valid
            is_valid = check_password_hash(user["password_hash"], password_current)
            if not is_valid:
                raise errors.Unauthorized()
        else:
            # user is trying to set other user's password
            # check permission
            if not token.get_permission("users", "change_password"):
                raise errors.NotEnoughPrivilege()

        # get new password
        password_new = request_json.get("new", None)
        if password_new is None:
            raise errors.BadRequest()

        # set new password
        matched_count = (
            Users()
            .update_one(
                query, {"$set": {"password_hash": generate_password_hash(password_new)}}
            )
            .matched_count
        )

        # send response
        if matched_count == 0:
            raise errors.NotFound()
        return Response(status=HTTPStatus.NO_CONTENT)
