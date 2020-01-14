from http import HTTPStatus

from flask import Flask, Response, jsonify, make_response
from jwt import exceptions as jwt_exceptions

from errors import oauth2, http
import marshmallow.exceptions


def register_handlers(app: Flask):
    app.errorhandler(BadRequest)(BadRequest.handler)
    app.errorhandler(OfflinerConfigNotValid)(OfflinerConfigNotValid.handler)
    app.errorhandler(Unauthorized)(Unauthorized.handler)
    app.errorhandler(NotFound)(NotFound.handler)
    app.errorhandler(InternalError)(InternalError.handler)

    app.errorhandler(oauth2.OAuth2Base)(oauth2.handler)
    app.errorhandler(http.HTTPBase)(http.handler)

    @app.errorhandler(marshmallow.exceptions.ValidationError)
    def handler_validationerror(e):
        return make_response(jsonify({"message": e.messages}), HTTPStatus.BAD_REQUEST)

    @app.errorhandler(jwt_exceptions.ExpiredSignature)
    def handler_expiredsig(_):
        return make_response(
            jsonify({"error": "token expired"}), HTTPStatus.UNAUTHORIZED
        )

    @app.errorhandler(jwt_exceptions.InvalidTokenError)
    def handler_invalidtoken(_):
        return make_response(
            jsonify({"error": "token invalid"}), HTTPStatus.UNAUTHORIZED
        )


# 400
class BadRequest(Exception):
    def __init__(self, message: str = None):
        self.message = message

    @staticmethod
    def handler(e):
        if isinstance(e, BadRequest) and e.message is not None:
            return make_response(jsonify({"error": e.message}), HTTPStatus.BAD_REQUEST)
        return Response(status=HTTPStatus.BAD_REQUEST)


class OfflinerConfigNotValid(Exception):
    def __init__(self):
        self.errors = {}

    @staticmethod
    def handler(e):
        if isinstance(e, OfflinerConfigNotValid):
            return make_response(jsonify(e.errors), HTTPStatus.BAD_REQUEST)
        return Response(status=HTTPStatus.BAD_REQUEST)


# 401
class Unauthorized(Exception):
    def __init__(self, message: str = None):
        self.message = message

    @staticmethod
    def handler(e):
        if isinstance(e, Unauthorized) and e.message is not None:
            return make_response(jsonify({"error": e.message}), HTTPStatus.UNAUTHORIZED)
        return Response(status=HTTPStatus.UNAUTHORIZED)


class NotEnoughPrivilege(Unauthorized):
    def __init__(self, permission):
        super().__init__(
            "you needs {} permission to perform this operation".format(
                permission if permission else "a"
            )
        )


# 404
class NotFound(Exception):
    def __init__(self, message: str = None):
        self.message = message

    @staticmethod
    def handler(e):
        if isinstance(e, NotFound) and e.message is not None:
            return make_response(jsonify({"error": e.message}), HTTPStatus.NOT_FOUND)
        return Response(status=HTTPStatus.NOT_FOUND)


# 500
class InternalError(Exception):
    @staticmethod
    def handler(e):
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)
