from enum import Enum


class Task(Enum):
    PENDING = 0
    PREPARING = 1
    GENERATING = 2
    UPLOADING = 3
    FINISHED = 4
    ERROR = 100

    def __lt__(self, other):
        if isinstance(other, Task):
            return self.value < other.value
        else:
            raise NotImplemented

    def __ge__(self, other):
        if isinstance(other, Task):
            return self.value >= other.value
        else:
            raise NotImplemented