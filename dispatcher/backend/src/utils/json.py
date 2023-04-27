from datetime import datetime
from json import JSONEncoder
from uuid import UUID

from bson.objectid import ObjectId
from flask.json.provider import DefaultJSONProvider


class ZimfarmJsonEncoder(JSONEncoder):
    """Encoder to use outside flask to encode custom types in JSON"""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat() + "Z"
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, ObjectId):
            return str(o)
        super().default(o)


class ZimfarmJsonProvider(DefaultJSONProvider):
    """Provider for Flask application to encode custom types in JSON"""

    @staticmethod
    def default(object_):
        if isinstance(object_, datetime):
            return object_.isoformat() + "Z"
        if isinstance(object_, UUID):
            return str(object_)
        if isinstance(object_, ObjectId):
            return str(object_)
        return DefaultJSONProvider.default(object_)
