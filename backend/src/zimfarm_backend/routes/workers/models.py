from zimfarm_backend.common.enums import Offliner
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
    offliners: list[Offliner]
    platforms: dict[str, int] | None = None  # mapping of platforms to max tasks
