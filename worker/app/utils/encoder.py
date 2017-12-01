import json
from datetime import datetime, timedelta
from utils.status import Status


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, timedelta):
            return o.microseconds
        elif isinstance(o, datetime):
            return o.isoformat() + 'Z'
        elif isinstance(o, bytes):
            return o.decode('utf-8')
        elif isinstance(o, Status):
            return o.name
        else:
            return json.JSONEncoder.default(self, o)
