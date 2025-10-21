from http import HTTPStatus
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    status_code: HTTPStatus
    success: bool
    data: T | None = None
