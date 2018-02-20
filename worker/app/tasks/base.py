from enum import Enum
from celery.task import Task
from celery.utils.log import get_task_logger


class Base(Task):
    """Base class for all zimfarm celery tasks.
    """

    abstract = True

    def __init__(self):
        super().__init__()
        self.logger = get_task_logger(__name__)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.logger.error("task failed")


class TaskFailed(Exception):
    def __init__(self, results):
        self.results = results


class TaskStatus(Enum):
    PENDING = 0
    PREPARING = 1
    GENERATING = 2
    UPLOADING = 3
    FINISHED = 4
    ERROR = 100