import logging
from http import HTTPStatus
from typing import Generic, TypeVar

from pydantic import BaseModel

from healthcheck.constants import DEBUG

# This is a special logger for status checks. It accepts the custom `checkname`.
# The field is set via extra whenever called to populate the log record.
# As per the docs, if any custom fields are omitted, the message will not
# be logged because a string formatting exception will occur.
status_logger = logging.getLogger("healthcheck.status")
# prevent propagation to the root logger
status_logger.propagate = False
status_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(asctime)s: %(levelname)s : %(checkname)s] %(message)s")
)
status_logger.addHandler(handler)


T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    status_code: HTTPStatus
    success: bool
    data: T | None = None
