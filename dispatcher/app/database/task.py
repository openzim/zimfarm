from app import db


class Task(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    args = db.Column(db.String)
    kwargs = db.Column(db.String)

    def __repr__(self):
        return "<Task(id='{id}', name={name}, args={args}, kwargs={kwargs})>".format(
            id=self.id,
            name=self.name,
            args=self.args,
            kwargs=self.kwargs
        )
db.create_all()


def add(id: str, name: str):
    task = Task(id=id, name=name)
    db.session.add(task)
    db.session.commit()


def get_all() -> [Task]:
    return Task.query.all()