from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Task


def get_task_by_id_or_none(session: OrmSession, task_id: UUID) -> Task | None:
    return session.scalars(select(Task).where(Task.id == task_id)).one_or_none()


def get_task_by_id(session: OrmSession, task_id: UUID) -> Task:
    if (task := get_task_by_id_or_none(session, task_id)) is None:
        raise RecordDoesNotExistError(f"Task with id {task_id} does not exist")
    return task
