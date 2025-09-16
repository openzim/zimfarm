import os
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.routes import (
    auth,
    contexts,
    healthcheck,
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
from zimfarm_backend.routes.http_errors import BadRequestError
from zimfarm_backend.utils.database import (
    create_initial_user,
    upgrade_db_schema,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    upgrade_db_schema()
    create_initial_user()
    yield


def create_app(*, debug: bool = True):
    app = FastAPI(
        debug=debug,
        docs_url="/",
        title="Zimfarm API",
        version="2.0.0",
        description="Zimfarm API for managing tasks, workers, and other resources",
        lifespan=lifespan,
    )

    if origins := os.getenv("ALLOWED_ORIGINS", None):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins.split(","),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    main_router = APIRouter(prefix="/v2")
    main_router.include_router(router=healthcheck.router)
    main_router.include_router(router=auth.router)
    main_router.include_router(router=contexts.router)
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


@app.exception_handler(ValidationError)
async def validation_error_handler(_, exc: ValidationError):
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


@app.exception_handler(RecordDoesNotExistError)
async def record_does_not_exist_error_handler(_, exc: RecordDoesNotExistError):
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(RecordAlreadyExistsError)
async def record_already_exists_error_handler(_, exc: RecordAlreadyExistsError):
    return JSONResponse(
        status_code=HTTPStatus.CONFLICT,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(BadRequestError)
async def bad_request_error_handler(_, exc: BadRequestError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "errors": exc.errors},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code, content={"success": False, "message": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_error_handler(_, __):  # pyright: ignore
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Internal server error"},
    )
