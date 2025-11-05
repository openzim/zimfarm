from typing import Literal

from zimfarm_backend.common.enums import DockerImageName
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import NotEmptyString
from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema


class OfflinerCreateSchema(BaseModel):
    offliner_id: NotEmptyString
    base_model: Literal["CamelModel", "DashModel"]
    docker_image_name: DockerImageName
    ci_secret_hash: NotEmptyString
    command_name: NotEmptyString


class OfflinerDefinitionCreateSchema(BaseModel):
    version: NotEmptyString
    ci_secret: NotEmptyString
    spec: OfflinerSpecSchema
