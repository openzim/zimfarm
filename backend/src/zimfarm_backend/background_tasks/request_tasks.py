from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.utils.scheduling import request_tasks_using_schedule


def request_tasks(session: OrmSession):
    """Request tasks using schedule"""
    logger.info("running periodic scheduler")
    request_tasks_using_schedule(session)
