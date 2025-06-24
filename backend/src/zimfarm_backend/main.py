from fastapi import APIRouter, FastAPI

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
