from http import HTTPStatus
from typing import Optional

from flask import jsonify


class HTTPBase(Exception):
    def __init__(
        self, status_code: HTTPStatus, error: str, description: Optional[str] = None
    ):
        self.status_code = status_code
        self.error = error
        self.description = description


def handler(error: HTTPBase):
    response = {"error": error.error}
    if error.description is not None:
        response["error_description"] = error.description

    response = jsonify(response)
    response.status_code = error.status_code.value
    return response


class InvalidRequestJSON(HTTPBase):
    def __init__(self, description: Optional[str] = None):
        super().__init__(HTTPStatus.BAD_REQUEST, "Invalid Request JSON", description)


class ResourceNotFound(HTTPBase):
    def __init__(self, error: str):
        if error is None:
            error = "Resource Not Found"
        super().__init__(HTTPStatus.NOT_FOUND, error)


class ScheduleNotFound(ResourceNotFound):
    def __init__(self):
        super().__init__("Schedule Not Found")


class TaskNotFound(ResourceNotFound):
    def __init__(self):
        super().__init__("Task Not Found")
