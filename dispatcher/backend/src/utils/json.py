from uuid import UUID
from datetime import datetime

from bson.objectid import ObjectId
from flask.json import JSONEncoder


class Encoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat() + "Z"
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, ObjectId):
            return str(o)
        super().default(o)
