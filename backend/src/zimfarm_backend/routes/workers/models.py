from ipaddress import IPv4Address, IPv6Address

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    ZIMDisk,
    ZIMMemory,
)


class WorkerCheckInSchema(BaseModel):
    """
    Schema for checking in a worker.
    """

    selfish: bool | None = None
    cpu: ZIMCPU
    memory: ZIMMemory
    disk: ZIMDisk
    offliners: list[str]
    platforms: dict[str, int] | None = None  # mapping of platforms to max tasks
    cordoned: bool | None = None


class WorkerUpdateSchema(BaseModel):
    """
    Schema for updating a worker.
    """

    contexts: dict[str, IPv4Address | IPv6Address | None] | None = None
    admin_disabled: bool | None = None
