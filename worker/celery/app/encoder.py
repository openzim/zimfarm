import json
from datetime import datetime, timedelta


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, timedelta):
            return o.microseconds
        elif isinstance(o, datetime):
            return o.isoformat() + 'Z'
        elif isinstance(o, bytes):
            return o.decode('utf-8')
        else:
            return json.JSONEncoder.default(self, o)
