from datetime import datetime, timedelta
from typing import Union
from uuid import uuid4, UUID

from bson import ObjectId
from flask import request, jsonify, Response
from werkzeug.security import check_password_hash

from common.mongo import Users, RefreshTokens
from utils.token import LoadedAccessToken
from errors.oauth2 import InvalidRequest, InvalidGrant, UnsupportedGrantType


class OAuth2:
    def __call__(self):
        """Handles OAuth2 authentication"""

        # get grant_type
        if request.is_json:
            grant_type = request.json.get("grant_type")
        elif request.mimetype == "application/x-www-form-urlencoded":
            grant_type = request.form.get("grant_type")
        else:
            grant_type = request.headers.get("grant_type")

        if grant_type == "password":
            # password grant
            if request.is_json:
                username = request.json.get("username")
                password = request.json.get("password")
            elif request.mimetype == "application/x-www-form-urlencoded":
                username = request.form.get("username")
                password = request.form.get("password")
            else:
                username = request.headers.get("username")
                password = request.headers.get("password")

            if username is None:
                raise InvalidRequest('Request was missing the "username" parameter.')
            if password is None:
                raise InvalidRequest('Request was missing the "password" parameter.')

            return self.password_grant(username, password)

        if grant_type == "refresh_token":
            # refresh token grant
            if request.is_json:
                refresh_token = request.json.get("refresh_token")
            elif request.mimetype == "application/x-www-form-urlencoded":
                refresh_token = request.form.get("refresh_token")
            else:
                refresh_token = request.headers.get("refresh_token")

            if refresh_token is None:
                raise InvalidRequest(
                    'Request was missing the "refresh_token" parameter.'
                )

            try:
                refresh_token = UUID(refresh_token)
            except ValueError:
                raise InvalidGrant("Refresh token is invalid.")

            return self.refresh_token_grant(refresh_token)
        # unknown grant
        raise UnsupportedGrantType(
            "{} is not a supported grant type.".format(grant_type)
        )

    @staticmethod
    def password_grant(username: str, password: str):
        """Implements logic for password grant."""

        # check user exists
        user = Users().find_one({"username": username})
        if user is None:
            raise InvalidGrant("Username or password is invalid.")

        # check password is valid
        password_hash = user.pop("password_hash")
        is_valid = check_password_hash(password_hash, password)
        if not is_valid:
            raise InvalidGrant("Username or password is invalid.")

        # generate token
        access_token = LoadedAccessToken(
            user["_id"], user["username"], user.get("scope", {})
        ).encode()
        refresh_token = OAuth2.generate_refresh_token(user["_id"])

        return OAuth2.success_response(access_token, refresh_token)

    @staticmethod
    def refresh_token_grant(old_refresh_token: UUID):
        """Implements logic for refresh token grant."""

        # check token exists in database and get expire time and user id
        collection = RefreshTokens()
        old_token_document = collection.find_one(
            {"token": old_refresh_token}, {"expire_time": 1, "user_id": 1}
        )
        if old_token_document is None:
            raise InvalidGrant("Refresh token is invalid.")

        # check token is not expired
        expire_time = old_token_document["expire_time"]
        if expire_time < datetime.now():
            raise InvalidGrant("Refresh token is expired.")

        # check user exists
        user_id = old_token_document["user_id"]
        user = Users().find_one({"_id": user_id}, {"password_hash": 0})
        if user is None:
            raise InvalidGrant("Refresh token is invalid.")

        # generate token
        access_token = LoadedAccessToken(
            user["_id"], user["username"], user.get("scope", {})
        ).encode()
        refresh_token = OAuth2.generate_refresh_token(user["_id"])

        # delete old refresh token from database
        collection.delete_one({"token": old_refresh_token})
        collection.delete_many({"expire_time": {"$lte": datetime.now()}})

        return OAuth2.success_response(access_token, refresh_token)

    @staticmethod
    def generate_refresh_token(user_id: ObjectId) -> UUID:
        """Generate and store refresh token in database.

        :param user_id: id of user to associate the refresh token with
        :return: a UUID4 refresh token
        """

        refresh_token = uuid4()
        RefreshTokens().insert_one(
            {
                "token": refresh_token,
                "user_id": user_id,
                "expire_time": datetime.now() + timedelta(days=30),
            }
        )
        return refresh_token

    @staticmethod
    def success_response(
        access_token: str, refresh_token: Union[str, UUID]
    ) -> Response:
        """Create a response when grant success."""

        if isinstance(refresh_token, UUID):
            refresh_token = str(refresh_token)

        response = jsonify(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": int(LoadedAccessToken.expire_time_delta.total_seconds()),
                "refresh_token": refresh_token,
            }
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return response
