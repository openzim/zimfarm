from enum import Enum


class TaskStatus(Enum):
    PENDING = 0
    PREPARING = 1
    GENERATING = 2
    UPLOADING = 3
    FINISHED = 4
    ERROR = 100
