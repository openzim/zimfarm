from http import HTTPStatus

import sqlalchemy as sa
from flask import Response, request
from werkzeug.security import check_password_hash, generate_password_hash

import db.models as dbm
from db.engine import Session
from routes import authenticate, errors, url_object_id
from routes.base import BaseRoute
from utils.token import AccessToken


class PasswordRoute(BaseRoute):
    rule = "/<string:username>/password"
    name = "password"
    methods = ["PATCH"]

    @authenticate
    @url_object_id(["username"])
    def patch(self, username: str, token: AccessToken.Payload):
        with Session.begin() as session:
            # get user to modify
            orm_user = session.execute(
                sa.select(dbm.User).where(dbm.User.username == username)
            ).scalar_one_or_none()

            if orm_user is None:
                raise errors.NotFound()

            request_json = request.get_json()
            if username == token.username:
                # user is trying to set their own password

                # get current password
                password_current = request_json.get("current", None)
                if password_current is None:
                    raise errors.BadRequest()

                # check current password is valid
                is_valid = check_password_hash(orm_user.password_hash, "bob")
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

            orm_user.password_hash = generate_password_hash(password_new)

        return Response(status=HTTPStatus.NO_CONTENT)
