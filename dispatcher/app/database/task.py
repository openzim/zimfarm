from datetime import datetime
from app import db


class Task(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    status = db.Column(db.String)
    created_time = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)
    args = db.Column(db.String)
    kwargs = db.Column(db.String)
    stdout = db.Column(db.String)

    def __repr__(self):
        return "<Task(id='{id}', name={name}, args={args}, kwargs={kwargs})>".format(
            id=self.id,
            name=self.name,
            args=self.args,
            kwargs=self.kwargs
        )

db.create_all()


def add(id: str, name: str, start: datetime) -> Task:
    task = Task(id=id, name=name, start=start)
    db.session.add(task)
    db.session.commit()
    return task


def update(id: str, status: str, stdout: str, start: datetime, finish: datetime) -> Task:
    task = Task.query.filter_by(id=id).first()
    task.status = status
    task.stdout = stdout
    if status == 'STARTED':
        task.start_time = start
    elif start == 'FINISHED':
        task.finish_time = finish
    db.session.commit()
    return task


def get(id: str) -> Task:
    return Task.query.filter_by(id=id).first()


def get_all() -> [Task]:
    return Task.query.all()