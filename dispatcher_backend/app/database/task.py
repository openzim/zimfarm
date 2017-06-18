from datetime import datetime
from app import db
from .models import Task


def add(id: str, name: str, status: str) -> Task:
    task = Task(id=id, name=name, status=status, created_time=datetime.now())
    db.session.add(task)
    db.session.commit()
    return task


def update(id: str, status: str, command: str=None, return_code: int=None,  stdout: str=None, stderr: str=None, error: str=None) -> Task:
    task = Task.query.filter_by(id=id).first()

    task.status = status
    if command is not None: task.command = command
    if return_code is not None: task.return_code = return_code
    if stdout is not None: task.stdout = stdout
    if stderr is not None: task.stderr = stderr
    if error is not None: task.error = error

    if status == 'STARTED':
        task.started_time = datetime.now()
    elif status == 'SUCCESS' or 'ERROR' in status:
        task.finished_time = datetime.now()
    db.session.commit()
    return task


def get(id: str) -> Task:
    return Task.query.filter_by(id=id).first()


def get_all() -> [Task]:
    return Task.query.all()