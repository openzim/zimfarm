from http import HTTPStatus

from flask import request, jsonify, Response
from jsonschema import validate, ValidationError
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash
from marshmallow import Schema, fields, validate as mm_validate

from common.mongo import Users
from common.roles import get_role_for
from routes import authenticate, url_object_id, errors
from utils.token import AccessToken


def _add_role(user):
    user.update({"role": get_role_for(user.get("scope"))})
    return user


@authenticate
def list_all(*, token: AccessToken.Payload):
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
        .find(query, {"_id": 0, "username": 1, "email": 1})
        .skip(skip)
        .limit(limit)
    )
    # users = [user for user in cursor]
    users = list(map(_add_role, cursor))

    return jsonify(
        {"meta": {"skip": skip, "limit": limit, "count": count}, "items": users}
    )


@authenticate
def create(token: AccessToken.Payload):
    # check user permission
    if not token.get_permission("users", "create"):
        raise errors.NotEnoughPrivilege()

    # validate request json
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 1},
            "password": {"type": "string", "minLength": 6},
            "email": {"type": ["string", "null"]},
            "scope": {"type": "object"},
        },
        "required": ["username", "password"],
        "additionalProperties": False,
    }
    try:
        request_json = request.get_json()
        validate(request_json, schema)
    except ValidationError as error:
        raise errors.BadRequest(error.message)

    # generate password hash
    password = request_json.pop("password")
    request_json["password_hash"] = generate_password_hash(password)

    try:
        user_id = Users().insert_one(request_json).inserted_id
        return jsonify({"_id": user_id})
    except DuplicateKeyError:
        raise errors.BadRequest("User already exists")


@authenticate
@url_object_id("username")
def get(token: AccessToken.Payload, username: str):
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
def delete(token: AccessToken.Payload, username: str):
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
