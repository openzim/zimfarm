class RecordDoesNotExistError(Exception):
    """Raised when a record does not exist in the database"""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
