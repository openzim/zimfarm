from http import HTTPStatus

import flask
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, request
from werkzeug.security import check_password_hash

import db.models as dbm
from common import getnow
from db import dbsession
from routes import API_PATH, authenticate
from routes.auth import ssh, validate
from routes.auth.oauth2 import OAuth2
from routes.errors import BadRequest, Unauthorized
from utils.check import raise_if, raise_if_none
from utils.token import AccessToken


@dbsession
def credentials(session: so.Session):
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
    raise_if(username is None or password is None, BadRequest, "missing username")

    orm_user = dbm.User.get(session, username, Unauthorized, "this user does not exist")

    # check password is valid
    is_valid = check_password_hash(orm_user.password_hash, password)
    raise_if(not is_valid, Unauthorized, "password does not match")

    # generate token
    access_token = AccessToken.encode_db(orm_user)
    access_expires = AccessToken.get_expiry(access_token)
    refresh_token = OAuth2.generate_refresh_token(orm_user.id, session)

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


@dbsession
def refresh_token(session: so.Session):
    """
    Issue a new set of access and refresh token after validating an old refresh token
    Old refresh token can only be used once and hence is removed from database
    Unused but expired refresh token is also deleted from database
    """

    # get old refresh token from request header
    old_token = request.headers.get("refresh-token")
    raise_if_none(old_token, BadRequest, "missing refresh-token")

    # check token exists in database and get expire time and user id
    old_token_document = session.execute(
        sa.select(dbm.Refreshtoken).where(dbm.Refreshtoken.token == old_token)
    ).scalar_one_or_none()
    raise_if_none(old_token_document, Unauthorized, "refresh-token invalid")

    # check token is not expired
    expire_time = old_token_document.expire_time
    raise_if(expire_time < getnow(), Unauthorized, "token expired")

    # check user exists
    orm_user = session.execute(
        sa.select(dbm.User).where(dbm.User.id == old_token_document.user_id)
    ).scalar_one_or_none()
    dbm.User.check(orm_user, Unauthorized, "user not found")

    # generate token
    access_token = AccessToken.encode_db(orm_user)
    refresh_token = OAuth2.generate_refresh_token(orm_user.id, session)

    # delete old refresh token from database
    session.delete(old_token_document)
    session.execute(
        sa.delete(dbm.Refreshtoken).where(dbm.Refreshtoken.expire_time < getnow())
    )

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
