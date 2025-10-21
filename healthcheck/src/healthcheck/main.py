from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from healthcheck.router import router


def create_app(*, debug: bool = True):
    app = FastAPI(
        debug=debug,
        docs_url="/",
        title="Zimfarm Healthcheck Service",
        version="1.0.0",
        description=(
            "Service for checking health status of Zimfarm components and dependencies"
        ),
    )

    main_router = APIRouter()
    main_router.include_router(router=router)

    app.include_router(router=main_router)

    # Serve package static files at /static (if present)
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


app = create_app()
