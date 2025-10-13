class RecordDoesNotExistError(Exception):
    """Raised when a record does not exist in the database"""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.detail = message


class RecordAlreadyExistsError(Exception):
    """Raised when a record already exists in the database"""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.detail = message


class RecordDisabledError(Exception):
    """Raised when a record is disabled"""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.detail = message
