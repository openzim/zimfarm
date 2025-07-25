from fastapi import APIRouter
from fastapi.responses import JSONResponse

from zimfarm_backend.common import getnow

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get("")
def get_languages() -> JSONResponse:
    return JSONResponse(content={"status": "ok", "timestamp": getnow().isoformat()})
