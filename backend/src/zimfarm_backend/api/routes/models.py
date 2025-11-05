from typing import Generic, TypeVar

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import Paginator

T = TypeVar("T")


class ListResponse(BaseModel, Generic[T]):
    meta: Paginator
    items: list[T]
