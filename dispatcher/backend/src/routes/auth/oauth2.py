from datetime import timedelta
from typing import Union
from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, request
from werkzeug.security import check_password_hash

import db.models as dbm
from common import getnow
from db.engine import Session
from errors.oauth2 import InvalidGrant, InvalidRequest, UnsupportedGrantType
from utils.token import LoadedAccessToken


class OAuth2:
    def __call__(self):
        """Handles OAuth2 authentication"""
        with Session.begin() as session:
            res = self.processCallWithSession(session=session)
        return res

    def processCallWithSession(self, session: so.Session):
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

            return self.password_grant(username, password, session)

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

            return self.refresh_token_grant(refresh_token, session)
        # unknown grant
        raise UnsupportedGrantType(
            "{} is not a supported grant type.".format(grant_type)
        )

    @staticmethod
    def password_grant(username: str, password: str, session: so.Session):
        """Implements logic for password grant."""

        orm_user = session.execute(
            sa.select(dbm.User).where(dbm.User.username == username)
        ).scalar_one_or_none()
        # check user exists
        if orm_user is None:
            raise InvalidGrant("Username or password is invalid.")

        # check password is valid
        is_valid = check_password_hash(orm_user.password_hash, password)
        if not is_valid:
            raise InvalidGrant("Username or password is invalid.")

        # generate token
        access_token = LoadedAccessToken(
            orm_user.id, orm_user.username, orm_user.scope or {}
        ).encode()
        refresh_token = OAuth2.generate_refresh_token(orm_user.id, session)

        return OAuth2.success_response(access_token, refresh_token)

    @staticmethod
    def refresh_token_grant(old_refresh_token: UUID, session: so.Session):
        """Implements logic for refresh token grant."""

        # check token exists in database and get expire time and user id
        old_token_document = session.execute(
            sa.select(dbm.Refreshtoken).where(
                dbm.Refreshtoken.token == old_refresh_token
            )
        ).scalar_one_or_none()
        if old_token_document is None:
            raise InvalidGrant("Refresh token is invalid.")

        # check token is not expired
        expire_time = old_token_document.expire_time
        if expire_time < getnow():
            raise InvalidGrant("Refresh token is expired.")

        # check user exists
        orm_user = session.execute(
            sa.select(dbm.User).where(dbm.User.id == old_token_document.user_id)
        ).scalar_one_or_none()
        if orm_user is None:
            raise InvalidGrant("Refresh token is invalid.")

        # generate token
        access_token = LoadedAccessToken(
            orm_user.id, orm_user.username, orm_user.scope or {}
        ).encode()
        refresh_token = OAuth2.generate_refresh_token(orm_user.id, session)

        # delete old refresh token from database
        session.delete(old_token_document)
        session.execute(
            sa.delete(dbm.Refreshtoken).where(dbm.Refreshtoken.expire_time < getnow())
        )

        return OAuth2.success_response(access_token, refresh_token)

    @staticmethod
    def generate_refresh_token(user_id: UUID, session: so.Session) -> UUID:
        """Generate and store refresh token in database.

        :param user_id: id of user to associate the refresh token with
        :return: a UUID4 refresh token
        """

        refresh_token = uuid4()

        # TODO: fetch "now" from database
        refresh_token_db = dbm.Refreshtoken(
            mongo_val=None,
            mongo_id=None,
            token=refresh_token,
            expire_time=getnow() + timedelta(days=30),
        )
        refresh_token_db.user_id = user_id
        session.add(refresh_token_db)
        return refresh_token

    @staticmethod
    def success_response(
        access_token: str, refresh_token: Union[str, dbm.Refreshtoken]
    ) -> Response:
        """Create a response when grant success."""

        if isinstance(refresh_token, dbm.Refreshtoken):
            refresh_token = refresh_token.token

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
