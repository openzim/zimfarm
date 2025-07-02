import os
from http import HTTPStatus

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from zimfarm_backend.routes import (
    auth,
    languages,
    offliners,
    platforms,
    requested_tasks,
    schedules,
    status,
    tags,
    tasks,
    users,
    workers,
)


def create_app(*, debug: bool = True):
    app = FastAPI(
        debug=debug,
        docs_url="/",
    )

    if origins := os.getenv("ALLOWED_ORIGINS", None):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins.split(","),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    main_router = APIRouter(prefix="/api/v2")
    main_router.include_router(router=auth.router)
    main_router.include_router(router=languages.router)
    main_router.include_router(router=platforms.router)
    main_router.include_router(router=offliners.router)
    main_router.include_router(router=users.router)
    main_router.include_router(router=requested_tasks.router)
    main_router.include_router(router=workers.router)
    main_router.include_router(router=tasks.router)
    main_router.include_router(router=tags.router)
    main_router.include_router(router=status.router)
    main_router.include_router(router=schedules.router)

    app.include_router(router=main_router)

    return app


app = create_app()


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_, exc: RequestValidationError):
    # transform the pydantic validation errors to a dictionary mapping
    # the field to the list of errors
    errors = {err["loc"][-1]: err["msg"] for err in exc.errors()}

    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Input values failed constraints validation",
            "errors": errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code, content={"success": False, "message": exc.detail}
    )
