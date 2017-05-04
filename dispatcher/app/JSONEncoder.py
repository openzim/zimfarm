from datetime import datetime
from flask.json import JSONEncoder
from database.task import Task


class ZimfarmDispatcherJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Task):
            json = {
                'id': o.id,
                'name': o.name,
                'status': o.status,
                'start': self.encode_datetime(o.start),
                'finish': self.encode_datetime(o.finished),
                'args': o.args,
                'kwargs': o.kwargs,
                'stdout': o.stdout,
            }
            return json
        else:
            JSONEncoder.default(self, o)

    def encode_datetime(self, d: datetime):
        return d.isoformat() + 'Z' if isinstance(d, datetime) else None
