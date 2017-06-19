from app import db


class Task(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    status = db.Column(db.String)

    created_time = db.Column(db.DateTime)
    started_time = db.Column(db.DateTime)
    finished_time = db.Column(db.DateTime)

    script = db.Column(db.String)
    return_code = db.Column(db.Integer)
    stdout = db.Column(db.String)
    stderr = db.Column(db.String)

    def __repr__(self):
        return "<Task(id='{id}', name={name}, args={args}, kwargs={kwargs})>".format(
            id=self.id,
            name=self.name,
            args=self.args,
            kwargs=self.kwargs
        )


class User(db.Model):
    username = db.Column(db.String, primary_key=True)
    password_hash = db.Column(db.String)