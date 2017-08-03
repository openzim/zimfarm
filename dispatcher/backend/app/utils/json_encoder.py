from datetime import datetime
from flask.json import JSONEncoder


class ZimfarmEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat() + 'Z'
        else:
            JSONEncoder.default(self, o)
