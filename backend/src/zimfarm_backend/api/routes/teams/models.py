from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)


class TeamsGetSchema(BaseModel):
    """Schema for filtering and paginating teams"""

    skip: SkipField = 0
    limit: LimitFieldMax200 = 20
    name: NotEmptyString | None = None
    is_private: bool | None = None


class RevertTeamSchema(BaseModel):
    """Schema for reverting a team to a previous history entry"""

    comment: NotEmptyString | None = None
