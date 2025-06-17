from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db.tasks import get_oldest_task_timestamp
from zimfarm_backend.routes.dependencies import gen_dbsession
from zimfarm_backend.routes.status.models import StatusMonitorName

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/{monitor_name}")
async def get_status(
    monitor_name: Annotated[StatusMonitorName, Path(..., description="Monitor name")],
    threshold_secs: Annotated[int, Query(..., description="Threshold in seconds")],
    status: Annotated[TaskStatus, Query(..., description=" Task status")],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
):
    """
    Get the Zimfarm status for a given monitor
    """
    match monitor_name:
        case StatusMonitorName.oldest_task_older_than:
            oldest_task_timestamp = get_oldest_task_timestamp(session, status)
            if (getnow() - oldest_task_timestamp).total_seconds() > threshold_secs:
                suffix = "KO"
            else:
                suffix = "OK"
            return Response(
                content=f"{monitor_name} for {status} and {threshold_secs}s: {suffix}",
                status_code=HTTPStatus.OK,
            )
