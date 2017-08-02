from datetime import datetime
from flask.json import JSONEncoder
from database.models import Task, User


class ZimfarmDispatcherJSONEncoder(JSONEncoder):
    def default(self, o):
        def encode_datetime(d: datetime):
            return d.isoformat() + 'Z' if isinstance(d, datetime) else None

        if isinstance(o, Task):
            json = {
                'id': o.id,
                'name': o.name,
                'status': o.status,
                'image_name': o.image_name,
                'script': o.script,
                'time': {
                    'created': encode_datetime(o.created_time),
                    'started': encode_datetime(o.started_time),
                    'finished': encode_datetime(o.finished_time)
                },
                'result': {
                    'return_code': o.return_code,
                    'stdout': o.stdout,
                    'stderr': o.stderr
                },
            }
            return json
        elif isinstance(o, User):
            return {
                'username': o.username,
                'scope': o.scope,
            }
        elif isinstance(o, datetime):
            return o.isoformat() + 'Z'
        else:
            JSONEncoder.default(self, o)
