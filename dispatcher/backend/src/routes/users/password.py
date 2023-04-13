from http import HTTPStatus

import sqlalchemy as sa
from flask import Response, request
from werkzeug.security import check_password_hash, generate_password_hash

import db.models as dbm
from db import dbsession
from routes import authenticate, errors, url_object_id
from routes.base import BaseRoute
from routes.utils import raise_if, raise_if_none
from utils.token import AccessToken


class PasswordRoute(BaseRoute):
    rule = "/<string:username>/password"
    name = "password"
    methods = ["PATCH"]

    @authenticate
    @dbsession
    @url_object_id(["username"])
    def patch(self, session, username: str, token: AccessToken.Payload):
        # get user to modify
        orm_user = session.execute(
            sa.select(dbm.User).where(dbm.User.username == username)
        ).scalar_one_or_none()

        raise_if_none(orm_user, errors.NotFound)

        request_json = request.get_json()
        if username == token.username:
            # user is trying to set their own password

            # get current password
            password_current = request_json.get("current", None)
            raise_if_none(password_current, errors.BadRequest)

            # check current password is valid
            is_valid = check_password_hash(orm_user.password_hash, password_current)
            raise_if(not is_valid, errors.Unauthorized)
        else:
            # user is trying to set other user's password
            # check permission
            raise_if(
                not token.get_permission("users", "change_password"),
                errors.NotEnoughPrivilege,
            )

        # get new password
        password_new = request_json.get("new", None)
        raise_if_none(password_new, errors.BadRequest)

        orm_user.password_hash = generate_password_hash(password_new)

        return Response(status=HTTPStatus.NO_CONTENT)
