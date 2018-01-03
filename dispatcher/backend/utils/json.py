from datetime import datetime
from flask.json import JSONEncoder
from bson.objectid import ObjectId


class Encoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat() + 'Z'
        elif isinstance(o, ObjectId):
            return str(o)
        else:
            super().default(o)
