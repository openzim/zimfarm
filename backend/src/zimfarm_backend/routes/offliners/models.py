from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import NotEmptyString
from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema


class OfflinerDefinitionCreateSchema(BaseModel):
    version: NotEmptyString
    ci_secret: NotEmptyString
    spec: OfflinerSpecSchema
