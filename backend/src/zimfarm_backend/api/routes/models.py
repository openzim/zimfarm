from typing import TypeVar

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import Paginator

T = TypeVar("T")


class ListResponse[T](BaseModel):
    meta: Paginator
    items: list[T]
