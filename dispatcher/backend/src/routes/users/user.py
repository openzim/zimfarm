from http import HTTPStatus

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, request
from marshmallow import ValidationError
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash

import db.models as dbm
from common.mongo import Users, Workers
from common.roles import ROLES, get_role_for
from common.schemas.parameters import (
    SkipLimitSchema,
    UserCreateSchema,
    UserUpdateSchema,
)
from db import engine
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

        with so.Session(engine) as session:
            count = session.query(dbm.User).count()
            sa.select(dbm.User)
            for user_obj in session.execute(
                sa.select(dbm.User)
                .offset(skip)
                .limit(limit)
                .options(so.selectinload(dbm.User.ssh_keys))
            ).scalars():
                print(user_obj.id)

        query = {}
        # count = Users().count_documents(query)
        cursor = (
            Users()
            .find(query, {"_id": 0, "username": 1, "email": 1, "scope": 1})
            .skip(skip)
            .limit(limit)
        )

        # add role to user while removing scope
        def _add_role(user):
            user.update({"role": get_role_for(user.pop("scope", {}))})
            return user

        users = list(map(_add_role, cursor))

        return jsonify(
            {"meta": {"skip": skip, "limit": limit, "count": count}, "items": users}
        )

    @authenticate
    @require_perm("users", "create")
    def post(self, token: AccessToken.Payload):
        try:
            request_json = UserCreateSchema().load(request.get_json())
        except ValidationError as e:
            raise errors.InvalidRequestJSON(e.messages)

        # generate password hash
        password = request_json.pop("password")
        request_json["password_hash"] = generate_password_hash(password)

        # fetch permissions
        request_json["scope"] = ROLES.get(request_json.pop("role"))

        try:
            user_id = Users().insert_one(request_json).inserted_id
            return jsonify({"_id": user_id})
        except DuplicateKeyError:
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

        # find user based on _id or username
        user = Users().find_one(
            {"username": username},
            {"_id": 0, "username": 1, "email": 1, "scope": 1, "ssh_keys": 1},
        )

        if user is None:
            raise errors.NotFound()

        user["role"] = get_role_for(user.get("scope"))

        return jsonify(user)

    @authenticate
    @require_perm("users", "update")
    @url_object_id("username")
    def patch(self, token: AccessToken.Payload, username: str):
        # find user based on username
        query = {"username": username}
        if Users().count_documents(query) != 1:
            raise errors.NotFound()

        try:
            request_json = UserUpdateSchema().load(request.get_json())
        except ValidationError as e:
            raise errors.BadRequest(e.messages)

        update = {}
        if "email" in request_json:
            update["email"] = request_json["email"]
        if "role" in request_json:
            update["scope"] = ROLES.get(request_json["role"])

        Users().update_one(query, {"$set": update})

        return Response(status=HTTPStatus.NO_CONTENT)

    @authenticate
    @require_perm("users", "delete")
    @url_object_id("username")
    def delete(self, token: AccessToken.Payload, username: str):
        # delete user
        deleted_count = Users().delete_one({"username": username}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()
        Workers().delete_many({"username": username})
        return Response(status=HTTPStatus.NO_CONTENT)
