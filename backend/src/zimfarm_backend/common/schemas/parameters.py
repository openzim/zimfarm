from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    WorkerField,
    ZIMDisk,
    ZIMMemory,
)


# requested-tasks for worker
class WorkerRequestedTaskSchema(BaseModel):
    worker: WorkerField
    avail_cpu: ZIMCPU
    avail_memory: ZIMMemory
    avail_disk: ZIMDisk
