from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    LimitFieldMax200,
    LimitFieldMax500,
    SkipField,
    WorkerField,
    ZIMDisk,
    ZIMMemory,
)


# languages GET
class SkipLimit500Schema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax500


# tags GET, # users GET, # workers GET
class SkipLimitSchema(BaseModel):
    skip: SkipField
    limit: LimitFieldMax200


# requested-tasks for worker
class WorkerRequestedTaskSchema(BaseModel):
    worker: WorkerField
    avail_cpu: ZIMCPU
    avail_memory: ZIMMemory
    avail_disk: ZIMDisk
