from http import HTTPStatus

import sqlalchemy as sa
from flask import Response, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

import common.schemas.orms as cso
import db.models as dbm
import errors.http as http_errors
from common.roles import ROLES
from common.schemas.parameters import (
    SkipLimitSchema,
    UserCreateSchema,
    UserUpdateSchema,
)
from db import count_from_stmt, dbsession
from routes import authenticate, errors, require_perm
from routes.base import BaseRoute
from utils.token import AccessToken


class UsersRoute(BaseRoute):
    rule = "/"
    name = "users"
    methods = ["GET", "POST"]

    @authenticate
    @dbsession
    @require_perm("users", "read")
    def get(self, token: AccessToken.Payload, session: Session):
        request_args = SkipLimitSchema().load(request.args.to_dict())
        skip, limit = request_args["skip"], request_args["limit"]

        # get users from database
        stmt = sa.select(dbm.User).filter(dbm.User.deleted == False)  # noqa: E712

        count = count_from_stmt(session, stmt)

        orm_users = session.execute(stmt.offset(skip).limit(limit)).scalars()

        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": count},
                "items": list(map(cso.UserSchemaReadMany().dump, orm_users)),
            }
        )

    @authenticate
    @dbsession
    @require_perm("users", "create")
    def post(self, token: AccessToken.Payload, session: Session):
        try:
            request_json = UserCreateSchema().load(request.get_json())
        except ValidationError as e:
            raise http_errors.InvalidRequestJSON(e.messages)

        orm_user = dbm.User(
            username=request_json["username"],
            email=request_json["email"],
            password_hash=generate_password_hash(request_json["password"]),
            scope=ROLES.get(request_json["role"]),
            deleted=False,
        )
        session.add(orm_user)

        try:
            session.flush()
        except IntegrityError:
            raise errors.BadRequest("User already exists")

        user_id = orm_user.id

        return jsonify({"_id": user_id})


class UserRoute(BaseRoute):
    rule = "/<string:username>"
    name = "user"
    methods = ["GET", "PATCH", "DELETE"]

    @authenticate
    @dbsession
    def get(self, token: AccessToken.Payload, session: Session, username: str):
        # if user in url is not user in token, check user permission
        if username != token.username:
            if not token.get_permission("users", "read"):
                raise errors.NotEnoughPrivilege()

        # find user based on username
        orm_user = dbm.User.get(session, username, errors.NotFound, fetch_ssh_keys=True)

        return jsonify(cso.UserSchemaReadOne().dump(orm_user))

    @authenticate
    @dbsession
    @require_perm("users", "update")
    def patch(self, token: AccessToken.Payload, session: Session, username: str):
        request_json = UserUpdateSchema().load(request.get_json())

        orm_user = dbm.User.get(session, username, errors.NotFound)

        if "email" in request_json:
            orm_user.email = request_json["email"]
        if "role" in request_json:
            orm_user.scope = ROLES.get(request_json["role"])

        return Response(status=HTTPStatus.NO_CONTENT)

    @authenticate
    @require_perm("users", "delete")
    @dbsession
    def delete(self, token: AccessToken.Payload, session: Session, username: str):
        # delete user

        orm_user = dbm.User.get(session, username, errors.NotFound)
        orm_user.deleted = True

        return Response(status=HTTPStatus.NO_CONTENT)
