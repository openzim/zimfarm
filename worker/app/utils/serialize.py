import json
from datetime import datetime, timedelta

from operations.error import OperationError


class ResultEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, timedelta):
            return o.microseconds
        elif isinstance(o, datetime):
            return o.isoformat() + 'Z'
        elif isinstance(o, bytes):
            return o.decode('utf-8')
        elif isinstance(o, OperationError):
            return o.to_dict()
        else:
            return json.JSONEncoder.default(self, o)
