from http import HTTPStatus

from flask import request, jsonify, Response
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash
from marshmallow import Schema, fields, validate as mm_validate, ValidationError

from common.mongo import Users
from common.roles import get_role_for, ROLES
from routes import authenticate, url_object_id, errors
from utils.token import AccessToken
from routes.base import BaseRoute


class UsersRoute(BaseRoute):
    rule = "/"
    name = "users"
    methods = ["GET", "POST"]

    @authenticate
    def get(self, token: AccessToken.Payload):
        # check user permission
        if not token.get_permission("users", "read"):
            raise errors.NotEnoughPrivilege()

        class SkipLimitSchema(Schema):
            skip = fields.Integer(
                required=False, missing=0, validate=mm_validate.Range(min=0)
            )
            limit = fields.Integer(
                required=False, missing=20, validate=mm_validate.Range(min=0, max=200)
            )

        request_args = SkipLimitSchema().load(request.args.to_dict())
        skip, limit = request_args["skip"], request_args["limit"]

        # get users from database
        query = {}
        count = Users().count_documents(query)
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
    def post(self, token: AccessToken.Payload):
        # check user permission
        if not token.get_permission("users", "create"):
            raise errors.NotEnoughPrivilege()

        # validate request json
        class UserCreateSchema(Schema):
            username = fields.String(required=True, validate=mm_validate.Length(min=1))
            password = fields.String(required=True, validate=mm_validate.Length(min=1))
            email = fields.Email(required=False)
            role = fields.String(
                required=True, validate=mm_validate.OneOf(ROLES.keys())
            )

        try:
            request_json = UserCreateSchema().load(request.get_json())
        except ValidationError as error:
            raise errors.InvalidRequestJSON(error.messages)

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
    @url_object_id("username")
    def patch(self, token: AccessToken.Payload, username: str):
        if not token.get_permission("users", "update"):
            raise errors.NotEnoughPrivilege()

        # find user based on username
        query = {"username": username}
        if Users().count_documents(query) != 1:
            raise errors.NotFound()

        class UpdateSchema(Schema):
            email = fields.Email(required=False)
            role = fields.String(
                required=False, validate=mm_validate.OneOf(ROLES.keys())
            )

        try:
            request_json = UpdateSchema().load(request.get_json())
        except ValidationError as error:
            raise errors.BadRequest(str(error.messages))

        update = {}
        if "email" in request_json:
            update["email"] = request_json["email"]
        if "role" in request_json:
            update["scope"] = ROLES.get(request_json["role"])

        Users().update_one(query, {"$set": update})

        return Response(status=HTTPStatus.NO_CONTENT)

    @authenticate
    @url_object_id("username")
    def delete(self, token: AccessToken.Payload, username: str):
        # if user in url is not user in token, check user permission
        if username != token.username:
            if not token.get_permission("users", "delete"):
                raise errors.NotEnoughPrivilege()

        # delete user
        deleted_count = Users().delete_one({"username": username}).deleted_count
        if deleted_count == 0:
            raise errors.NotFound()
        else:
            return Response(status=HTTPStatus.NO_CONTENT)
