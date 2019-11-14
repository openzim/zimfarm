from typing import Optional
from http import HTTPStatus

from flask import jsonify


class OAuth2Base(Exception):
    def __init__(
        self,
        status_code: HTTPStatus,
        error: str,
        description: str,
        uri: Optional[str] = None,
    ):
        self.status_code = status_code
        self.error = error
        self.description = description
        self.uri = uri


def handler(error: OAuth2Base):
    response = {"error": error.error}
    if error.description is not None:
        response["error_description"] = error.description
    if error.uri is not None:
        response["error_uri"] = error.uri

    response = jsonify(response)
    response.status_code = error.status_code.value
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


class InvalidRequest(OAuth2Base):
    """The request is missing a parameter so the server can’t proceed with the request."""

    def __init__(self, description: str):
        super().__init__(HTTPStatus.BAD_REQUEST, "invalid_request", description)


class InvalidGrant(OAuth2Base):
    """User's credential is invalid."""

    def __init__(self, description: str):
        super().__init__(HTTPStatus.UNAUTHORIZED, "invalid_grant", description)


class UnsupportedGrantType(OAuth2Base):
    """The authorization server doesn’t recognize the grant type in the request."""

    def __init__(self, description: str):
        super().__init__(HTTPStatus.BAD_REQUEST, "unsupported_grant_type", description)
