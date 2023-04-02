from http import HTTPStatus

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, request
from marshmallow import ValidationError
from pymongo.errors import DuplicateKeyError
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

import common.schemas.orms as cso
import db.models as dbm
from common.mongo import Users, Workers
from common.roles import ROLES, get_role_for
from common.schemas.parameters import (
    SkipLimitSchema,
    UserCreateSchema,
    UserUpdateSchema,
)
from db.engine import Session
from routes import authenticate, errors, require_perm, url_object_id
from routes.base import BaseRoute
from utils.token import AccessToken


class UsersRoute(BaseRoute):
    rule = "/"
    name = "users"
    methods = ["GET", "POST"]

    @authenticate
    @require_perm("users", "read")
    def get(self, token: AccessToken.Payload):
        request_args = SkipLimitSchema().load(request.args.to_dict())
        skip, limit = request_args["skip"], request_args["limit"]

        # get users from database
        with Session.begin() as session:
            count = session.query(dbm.User).count()

            orm_users = session.execute(
                sa.select(dbm.User).offset(skip).limit(limit)
            ).scalars()

            api_users = list(map(cso.UserSchemaReadMany().dump, orm_users))

            return jsonify(
                {
                    "meta": {"skip": skip, "limit": limit, "count": count},
                    "items": api_users,
                }
            )

    @authenticate
    @require_perm("users", "create")
    def post(self, token: AccessToken.Payload):
        request_json = UserCreateSchema().load(request.get_json())

        with Session.begin() as session:
            pgmUser = dbm.User(
                mongo_val=None,
                username=request_json["username"],
                email=request_json["email"],
                password_hash=generate_password_hash(request_json["password"]),
                scope=ROLES.get(request_json["role"]),
            )
            session.add(pgmUser)

            try:
                session.flush()
                return jsonify({"_id": pgmUser.id})
            except IntegrityError:
                raise errors.BadRequest("User already exists")


class UserRoute(BaseRoute):
    rule = "/<string:username>"
    name = "user"
    methods = ["GET", "PATCH", "DELETE"]

    @authenticate
    @url_object_id("username")
    def get(self, token: AccessToken.Payload, username: str):
        # if user in url is not user in token, check user permission
        if username != token.username:
            if not token.get_permission("users", "read"):
                raise errors.NotEnoughPrivilege()

        # find user based on username
        with Session.begin() as session:
            orm_user = session.execute(
                sa.select(dbm.User)
                .where(dbm.User.username == username)
                .options(so.selectinload(dbm.User.ssh_keys))
            ).scalar_one_or_none()

            if orm_user is None:
                raise errors.NotFound()

            api_user = cso.UserSchemaReadOne().dump(orm_user)

            return jsonify(api_user)

    @authenticate
    @require_perm("users", "update")
    @url_object_id("username")
    def patch(self, token: AccessToken.Payload, username: str):
        request_json = UserUpdateSchema().load(request.get_json())

        with Session.begin() as session:
            orm_user = session.execute(
                sa.select(dbm.User).where(dbm.User.username == username)
            ).scalar_one_or_none()

            if orm_user is None:
                raise errors.NotFound()

            if "email" in request_json:
                orm_user.email = request_json["email"]
            if "role" in request_json:
                orm_user.scope = ROLES.get(request_json["role"])

        return Response(status=HTTPStatus.NO_CONTENT)

    @authenticate
    @require_perm("users", "delete")
    @url_object_id("username")
    def delete(self, token: AccessToken.Payload, username: str):
        # delete user

        with Session.begin() as session:
            orm_user = session.execute(
                sa.delete(dbm.User)
                .where(dbm.User.username == username)
                .returning(dbm.User.id)
            ).scalar_one_or_none()
            if orm_user is None:
                raise errors.NotFound()

        # TODO: Delete workers associated with current user as well
        # Workers().delete_many({"username": username})
        return Response(status=HTTPStatus.NO_CONTENT)
