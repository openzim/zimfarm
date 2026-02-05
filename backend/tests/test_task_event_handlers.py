from collections.abc import Callable

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.utils import task_canceling_event_handler
from zimfarm_backend.db.models import Task


def test_task_canceling_event_handler(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
):
    task = create_task(status=TaskStatus.started)
    task.timestamp = [(TaskStatus.started, getnow())]
    dbsession.add(task)
    dbsession.flush()

    task_canceling_event_handler(dbsession, task.id, {})
    dbsession.refresh(task)
    assert task.status == TaskStatus.canceling
