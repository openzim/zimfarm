from typing import Any

from fastapi import HTTPException, status


class BadRequestError(HTTPException):
    def __init__(
        self, message: Any = None, errors: dict[str, str] | None = None
    ) -> None:
        if message is None:
            message = "Invalid request body"

        self.errors = errors
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class UnauthorizedError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = "Invalid authentication credentials"
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = "Identity unknown to server."
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class NotFoundError(HTTPException):
    def __init__(self, message: Any) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class UnsupportedContentTypeError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = "Unsupported content type."
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=message,
        )


class ServerError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = "The server encountered an error while processing the request."
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )


class ConflictError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = (
                "The request could not be completed due to a conflict with "
                "the current state of the resource."
            )
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


class ServiceUnavailableError(HTTPException):
    def __init__(self, message: Any = None) -> None:
        if message is None:
            message = (
                "The server is temporarily unable to service your request "
                "due to maintenance downtime or capacity problems. "
                "Please try again later."
            )
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )
