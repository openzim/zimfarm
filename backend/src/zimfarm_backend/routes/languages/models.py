from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import LanguageSchema, Paginator


class LanguageList(BaseModel):
    """Response model for list of languages with pagination metadata."""

    meta: Paginator
    items: list[LanguageSchema]
