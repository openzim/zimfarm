from enum import Enum


class TaskStatus(Enum):
    PENDING = 0
    EXECUTING = 1
    FINISHED = 2
    ERROR = 3

