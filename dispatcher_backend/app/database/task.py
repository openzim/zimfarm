from datetime import datetime
from app import db


class Task(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    status = db.Column(db.String)

    created_time = db.Column(db.DateTime)
    started_time = db.Column(db.DateTime)
    finished_time = db.Column(db.DateTime)

    command = db.Column(db.String)
    stdout = db.Column(db.String)
    stderr = db.Column(db.String)

    def __repr__(self):
        return "<Task(id='{id}', name={name}, args={args}, kwargs={kwargs})>".format(
            id=self.id,
            name=self.name,
            args=self.args,
            kwargs=self.kwargs
        )

db.create_all()


def add(id: str, name: str, status: str, command: str) -> Task:
    task = Task(id=id, name=name, status=status, command=command, created_time=datetime.now())
    db.session.add(task)
    db.session.commit()
    return task


def update(id: str, status: str, stdout: str, stderr: str) -> Task:
    task = Task.query.filter_by(id=id).first()
    task.status = status
    task.stdout = stdout
    task.stderr = stderr
    if status == 'STARTED':
        task.started_time = datetime.now()
    elif status == 'FINISHED' or status == 'ERROR':
        task.finished_time = datetime.now()
    db.session.commit()
    return task


def get(id: str) -> Task:
    return Task.query.filter_by(id=id).first()


def get_all() -> [Task]:
    return Task.query.all()