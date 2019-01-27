from typing import Optional


class OperationError(Exception):
    def to_dict(self):
        return {}


class OfflinerError(OperationError):
    def __init__(self, code: str, message: Optional[str] = None, stderr: Optional[bytes] = None):
        self.code = code
        self.message = message
        self.stderr = stderr

    def to_dict(self):
        return {
            'code': self.code,
            'message': self.message,
            'stderr': self.stderr
        }
