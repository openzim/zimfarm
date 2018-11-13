from celery.task import Task
from celery.utils.log import get_task_logger


class Base(Task):
    """Base class for all zimfarm celery tasks.
    """

    abstract = True
    resultrepr_maxsize = 1024000
    logger = get_task_logger(__name__)

    def __init__(self):
        super().__init__()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.logger.error("task failed")


class TaskFailed(Exception):
    pass
