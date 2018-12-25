from http import HTTPStatus

from flask import jsonify


class HTTPBase(Exception):
    def __init__(self, status_code: HTTPStatus, error: str, description: str):
        self.status_code = status_code
        self.error = error
        self.description = description


def handler(error: HTTPBase):
    response = {'error': error.error}
    if error.description is not None:
        response['error_description'] = error.description

    response = jsonify(response)
    response.status_code = error.status_code.value
    return response


class InvalidRequestJSON(HTTPBase):
    def __init__(self, description: str):
        super().__init__(HTTPStatus.BAD_REQUEST, 'Invalid Request JSON', description)


class ResourceNotFound(HTTPBase):
    def __init__(self, name: str):
        super().__init__(HTTPStatus.NOT_FOUND, '{} Not Found'.format(name))


class ScheduleNotFound(ResourceNotFound):
    def __init__(self):
        super().__init__('Schedule')
