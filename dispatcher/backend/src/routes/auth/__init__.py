from uuid import UUID, uuid4
from http import HTTPStatus
from datetime import datetime, timedelta

import flask
from flask import request, jsonify, Response
from werkzeug.security import check_password_hash

from .. import API_PATH, authenticate2
from . import validate, ssh
from common.mongo import Users, RefreshTokens
from utils.token import AccessToken
from ..errors import BadRequest, Unauthorized
from .oauth2 import OAuth2


def credentials():
    """
    Authorize a user with username and password
    When success, return json object with access and refresh token
    """

    # get username and password from request header
    if "application/x-www-form-urlencoded" in request.content_type:
        username = request.form.get("username")
        password = request.form.get("password")
    else:
        username = request.headers.get("username")
        password = request.headers.get("password")
    if username is None or password is None:
        raise BadRequest()

    # check user exists
    user = Users().find_one({"username": username})
    if user is None:
        raise Unauthorized()

    # check password is valid
    password_hash = user.pop("password_hash")
    is_valid = check_password_hash(password_hash, password)
    if not is_valid:
        raise Unauthorized()

    # generate token
    access_token = AccessToken.encode(user)
    refresh_token = uuid4()

    # store refresh token in database
    RefreshTokens().insert_one(
        {
            "token": refresh_token,
            "user_id": user["_id"],
            "expire_time": datetime.now() + timedelta(days=30),
        }
    )

    # send response
    response_json = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": timedelta(minutes=60).total_seconds(),
        "refresh_token": refresh_token,
    }
    response = jsonify(response_json)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


def refresh_token():
    """
    Issue a new set of access and refresh token after validating an old refresh token
    Old refresh token can only be used once and hence is removed from database
    Unused but expired refresh token is also deleted from database
    """

    # get old refresh token from request header
    old_token = request.headers.get("refresh-token")
    if old_token is None:
        raise BadRequest()

    # check token exists in database and get expire time and user id
    collection = RefreshTokens()
    old_token_document = collection.find_one(
        {"token": UUID(old_token)}, {"expire_time": 1, "user_id": 1}
    )
    if old_token_document is None:
        raise Unauthorized()

    # check token is not expired
    expire_time = old_token_document["expire_time"]
    if expire_time < datetime.now():
        raise Unauthorized("token expired")

    # check user exists
    user_id = old_token_document["user_id"]
    user = Users().find_one({"_id": user_id}, {"password_hash": 0})
    if user is None:
        raise Unauthorized()

    # generate token
    access_token = AccessToken.encode(user)
    refresh_token = uuid4()

    # store refresh token in database
    RefreshTokens().insert_one(
        {
            "token": refresh_token,
            "user_id": user["_id"],
            "expire_time": datetime.now() + timedelta(days=30),
        }
    )

    # delete old refresh token from database
    collection.delete_one({"token": UUID(old_token)})
    collection.delete_many({"expire_time": {"$lte": datetime.now()}})

    # send response
    response_json = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": timedelta(minutes=60).total_seconds(),
        "refresh_token": refresh_token,
    }
    response = jsonify(response_json)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@authenticate2
def test(token: AccessToken.Payload):
    return Response(status=HTTPStatus.NO_CONTENT)


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__("auth", __name__, url_prefix=f"{API_PATH}/auth")
        self.add_url_rule(
            "/authorize", "auth_with_credentials", credentials, methods=["POST"]
        )
        self.add_url_rule(
            "/ssh_authorize", "auth_with_ssh", ssh.asymmetric_key_auth, methods=["POST"]
        )
        self.add_url_rule("/test", "test_auth", test, methods=["GET"])
        self.add_url_rule("/token", "auth_with_token", refresh_token, methods=["POST"])
        self.add_url_rule("/oauth2", "oauth2", OAuth2(), methods=["POST"])
        self.add_url_rule(
            "/validate/ssh_key", "validate_ssh_key", validate.ssh_key, methods=["POST"]
        )
