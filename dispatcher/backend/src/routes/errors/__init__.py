from flask import Flask, Response, jsonify
from jwt import exceptions as jwt_exceptions

from errors import oauth2


def register_handlers(app: Flask):
    app.errorhandler(BadRequest)(BadRequest.handler)
    app.errorhandler(OfflinerConfigNotValid)(OfflinerConfigNotValid.handler)
    app.errorhandler(Unauthorized)(Unauthorized.handler)
    app.errorhandler(NotFound)(NotFound.handler)
    app.errorhandler(InternalError)(InternalError.handler)

    app.errorhandler(oauth2.OAuth2Base)(oauth2.handler)

    @app.errorhandler(jwt_exceptions.ExpiredSignature)
    def handler(_):
        response = jsonify({'error': 'token expired'})
        response.status_code = 401
        return response

    @app.errorhandler(jwt_exceptions.InvalidTokenError)
    def handler(_):
        response = jsonify({'error': 'token invalid'})
        response.status_code = 401
        return response


# 400
class BadRequest(Exception):
    def __init__(self, message: str=None):
        self.message = message

    @staticmethod
    def handler(e):
        if isinstance(e, BadRequest) and e.message is not None:
            response = jsonify({'error': e.message})
            response.status_code = 400
            return response
        else:
            return Response(status=400)


class OfflinerConfigNotValid(Exception):
    def __init__(self):
        self.errors = {}

    @staticmethod
    def handler(e):
        if isinstance(e, OfflinerConfigNotValid):
            response = jsonify(e.errors)
            response.status_code = 400
            return response
        else:
            return Response(status=400)


# 401
class Unauthorized(Exception):
    def __init__(self, message: str=None):
        self.message = message

    @staticmethod
    def handler(e):
        if isinstance(e, Unauthorized) and e.message is not None:
            response = jsonify({'error': e.message})
            response.status_code = 401
            return response
        else:
            return Response(status=401)


class NotEnoughPrivilege(Unauthorized):
    def __init__(self):
        super().__init__('you are not authorized to perform this operation')


# 404
class NotFound(Exception):
    def __init__(self, message: str=None):
        self.message = message

    @staticmethod
    def handler(e):
        if isinstance(e, NotFound) and e.message is not None:
            response = jsonify({'error': e.message})
            response.status_code = 404
            return response
        else:
            return Response(status=404)


# 500
class InternalError(Exception):
    @staticmethod
    def handler(e):
        return Response(status=500)
