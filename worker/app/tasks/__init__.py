from enum import Enum
from .MWOffliner import MWOffliner


class TaskStatus(Enum):
    PENDING = 0
    PREPARING = 1
    GENERATING = 2
    UPLOADING = 3
    FINISHED = 4
    ERROR = 100
