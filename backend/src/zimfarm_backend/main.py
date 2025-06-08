from fastapi import APIRouter, FastAPI

from zimfarm_backend.routes import auth, languages, platforms


def create_app(*, debug: bool = True):
    app = FastAPI(
        debug=debug,
        docs_url="/",
    )
    main_router = APIRouter(prefix="/api/v2")
    main_router.include_router(router=auth.router)
    main_router.include_router(router=languages.router)
    main_router.include_router(router=platforms.router)

    app.include_router(router=main_router)

    return app


app = create_app()
