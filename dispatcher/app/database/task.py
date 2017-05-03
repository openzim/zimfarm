from datetime import datetime
from app import db


class Task(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    status = db.Column(db.String)
    start = db.Column(db.DateTime)
    finished = db.Column(db.DateTime)
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


def update(id: str, status: str) -> Task:
    task = Task.query.filter_by(id=id).first()
    task.status = status
    db.session.commit()
    return task


def get(id: str) -> Task:
    return Task.query.filter_by(id=id).first()


def get_all() -> [Task]:
    return Task.query.all()