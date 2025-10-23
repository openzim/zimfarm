import datetime
from typing import Literal

from pydantic import BaseModel

from healthcheck.constants import ZIMFARM_API_URL
from healthcheck.requests import query_api
from healthcheck.status import Result


class Worker(BaseModel):
    name: str
    status: Literal["online", "offline"]
    last_seen: datetime.datetime | None = None


class WorkersStatus(BaseModel):
    workers: list[Worker]
    has_online_worker: bool


def check_worker_online(worker: Worker) -> bool:
    if worker.last_seen is None:
        return False
    return worker.status == "online"


async def get_workers_status() -> Result[WorkersStatus]:
    """Fetch the list of workers and check their online status."""
    response = await query_api(
        f"{ZIMFARM_API_URL}/workers", method="GET", params={"hide_offlines": "true"}
    )

    if not response.success:
        return Result(
            success=response.success,
            status_code=response.status_code,
            data=None,
        )

    workers = [Worker.model_validate(item) for item in response.json.get("items", [])]
    has_online = any(check_worker_online(worker) for worker in workers)

    return Result(
        success=len(workers) > 0,
        status_code=response.status_code,
        data=WorkersStatus(
            workers=workers,
            has_online_worker=has_online,
        ),
    )
