from enum import Enum


class ZimfarmGenericTaskStatus(Enum):
    PENDING = 0
    UPDATING_CONTAINER = 1
    EXECUTING_SCRIPT = 2
    UPLOADING_FILES = 3
    CLEANING_UP = 4
    FINISHED = 5
    ERROR = 100