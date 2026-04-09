from ipaddress import IPv4Address, IPv6Address
from typing import Annotated

from pydantic import Field

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    ZIMDisk,
    ZIMMemory,
)
from zimfarm_backend.common.schemas.models import DockerImageVersionSchema, KeySchema


class WorkerCheckInSchema(BaseModel):
    """
    Schema for checking in a worker.
    """

    selfish: bool | None = None
    cpu: ZIMCPU
    memory: ZIMMemory
    disk: ZIMDisk
    docker_image: DockerImageVersionSchema | None = None
    offliners: list[str]
    platforms: dict[str, int] | None = None  # mapping of platforms to max tasks
    cordoned: bool | None = None


class WorkerCheckInResponse(BaseModel):
    """
    Response schema for worker check-in.
    """

    worker_manager: DockerImageVersionSchema | None = None


class WorkerUpdateSchema(BaseModel):
    """
    Schema for updating a worker.
    """

    contexts: dict[str, IPv4Address | IPv6Address | None] | None = None
    admin_disabled: bool | None = None


WorkerName = Annotated[
    str,
    Field(
        pattern=r"^[a-z0-9-]+$",
        min_length=3,
    ),
]


class WorkerCreateSchema(BaseModel):
    """
    Schema for creating a worker.
    """

    name: WorkerName
    ssh_key: KeySchema
