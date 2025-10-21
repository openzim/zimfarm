import os
from asyncio import gather
from collections.abc import Callable
from http import HTTPStatus

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from healthcheck.status.auth import authenticate
from healthcheck.status.database import (
    check_database_connection,
)
from healthcheck.status.workers import get_workers_status

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


def status_class(success: bool) -> str:  # noqa: FBT001
    return "text-success" if success else "text-danger"


def status_text(success: bool) -> str:  # noqa: FBT001
    return "Operational" if success else "Issue Detected"


# Register custom template filters
filters: list[tuple[str, Callable[..., str]]] = [
    ("status_class", status_class),
    ("status_text", status_text),
]
for name, func in filters:
    templates.env.filters[name] = func  # type: ignore


@router.get("/")
async def healthcheck(request: Request) -> HTMLResponse:
    auth_check, db_check, workers_check = await gather(
        authenticate(),
        check_database_connection(),
        get_workers_status(),
    )

    global_status = all(
        [
            auth_check.success,
            db_check.success,
            workers_check.success,
        ]
    )

    return templates.TemplateResponse(
        "healthcheck.html",
        {
            "request": request,
            "global_status": global_status,
            "auth": auth_check,
            "database": db_check,
            "workers": workers_check,
        },
        status_code=HTTPStatus.OK if global_status else HTTPStatus.SERVICE_UNAVAILABLE,
    )
