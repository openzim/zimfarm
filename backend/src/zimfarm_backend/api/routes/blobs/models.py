from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)


class CreateBlobRequest(BaseModel):
    flag_name: NotEmptyString
    kind: NotEmptyString
    data: NotEmptyString
    comments: str | None = None


class UpdateBlobRequest(BaseModel):
    comments: str | None = None


class BlobsGetSchema(BaseModel):
    skip: SkipField = 0
    limit: LimitFieldMax200 = 20
