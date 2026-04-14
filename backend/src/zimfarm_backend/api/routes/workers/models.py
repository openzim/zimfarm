from ipaddress import IPv4Address, IPv6Address

from pydantic import computed_field, field_validator

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    NotEmptyString,
    ZIMDisk,
    ZIMMemory,
)
from zimfarm_backend.common.schemas.models import DockerImageVersionSchema


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


class KeySchema(BaseModel):
    """
    Schema for creating a ssh key
    """

    key: NotEmptyString

    @field_validator("key", mode="after")
    @classmethod
    def validate_key(cls, value: str) -> str:
        value = value.strip()
        if len(value.split(" ")) != 3:  # noqa: PLR2004
            raise ValueError("Key does not appear to be an SSH public file.")
        return value

    @computed_field
    @property
    def name(self) -> str:
        return self.key.split(" ")[2]
