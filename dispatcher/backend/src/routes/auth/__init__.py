import datetime
from uuid import UUID, uuid4
from http import HTTPStatus

import flask
from bson.binary import UUIDLegacy
from flask import request, jsonify, Response
from werkzeug.security import check_password_hash

from utils.token import AccessToken
from common import getnow
from common.mongo import Users, RefreshTokens
from common.constants import REFRESH_TOKEN_EXPIRY
from routes import API_PATH, authenticate
from routes.auth import validate, ssh
from routes.auth.oauth2 import OAuth2
from routes.errors import BadRequest, Unauthorized


def create_refresh_token(username):
    token = uuid4()
    RefreshTokens().insert_one(
        {
            "token": token,
            "username": username,
            "expire_time": getnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY),
        }
    )

    # delete old refresh token from database
    RefreshTokens().delete_many({"expire_time": {"$lte": getnow()}})

    return token


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
        raise BadRequest("missing username or password")

    # check user exists
    user = Users().find_one(
        {"username": username}, {"username": 1, "scope": 1, "password_hash": 1}
    )
    if user is None:
        raise Unauthorized("this user does not exist")

    # check password is valid
    password_hash = user.pop("password_hash")
    is_valid = check_password_hash(password_hash, password)
    if not is_valid:
        raise Unauthorized("password does not match")

    # generate token
    access_token = AccessToken.encode(user)
    access_expires = AccessToken.get_expiry(access_token)
    refresh_token = create_refresh_token(user["username"])

    # send response
    response_json = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_expires,
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
        raise BadRequest("missing refresh-token")

    # check token exists in database and get expire time and user id
    try:
        old_token_document = RefreshTokens().find_one(
            {"token": UUIDLegacy(UUID(old_token))}, {"expire_time": 1, "username": 1}
        )
        if old_token_document is None:
            raise Unauthorized("refresh-token invalid")
    except Exception:
        raise Unauthorized("refresh-token invalid")

    # check token is not expired
    if old_token_document["expire_time"] < getnow():
        raise Unauthorized("token expired")

    # check user exists
    user = Users().find_one(
        {"username": old_token_document["username"]}, {"username": 1, "scope": 1}
    )
    if user is None:
        raise Unauthorized("user not found")

    # generate token
    access_token = AccessToken.encode(user)
    refresh_token = create_refresh_token(user["username"])
    # delete old refresh token from database
    RefreshTokens().delete_one({"token": UUID(old_token)})

    # send response
    response_json = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": AccessToken.get_expiry(access_token),
        "refresh_token": refresh_token,
    }
    response = jsonify(response_json)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@authenticate
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
