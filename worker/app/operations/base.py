from typing import Optional


class Operation:
    """Base class for all operations"""

    def __init__(self):
        pass

    def execute(self):
        pass


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


class UploadError(OperationError):
    def __init__(self, code: str, message: Optional[str] = None):
        self.code = code
        self.message = message

    def to_dict(self):
        return {
            'code': self.code,
            'message': self.message,
        }
