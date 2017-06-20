from datetime import datetime
from app import db
from .models import Task
from status import ZimfarmGenericTaskStatus


def add(id: str, name: str, status: ZimfarmGenericTaskStatus, script: str) -> Task:
    task = Task(id=id, name=name, status=status.name, created_time=datetime.now(), script=script)
    db.session.add(task)
    db.session.commit()
    return task


def update(id: str, new_status: ZimfarmGenericTaskStatus, stdout: str=None, stderr: str=None, return_code=None) -> Task:
    task = Task.query.filter_by(id=id).first()

    old_status = ZimfarmGenericTaskStatus[task.status]
    if old_status.value > new_status.value:
        return

    task.status = new_status.name
    task.stdout = stdout
    task.stderr = stderr
    task.return_code = return_code

    if new_status.value > ZimfarmGenericTaskStatus.PENDING.value and task.started_time is None:
        task.started_time = datetime.now()

    if new_status == ZimfarmGenericTaskStatus.FINISHED or new_status == ZimfarmGenericTaskStatus.ERROR:
        task.finished_time = datetime.now()

    db.session.commit()
    return task


def get(id: str) -> Task:
    return Task.query.filter_by(id=id).first()


def get_all() -> [Task]:
    return Task.query.all()