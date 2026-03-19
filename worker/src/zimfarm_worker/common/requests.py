import datetime
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

import requests

from zimfarm_worker.common import logger
from zimfarm_worker.common.constants import REQUESTS_TIMEOUT


@dataclass
class Token:
    """Access token on successful authentication."""

    access_token: str
    expires_time: datetime.datetime
    refresh_token: str
    token_type: str = "Bearer"


@dataclass
class Response:
    """A response from the webapi"""

    status_code: int
    success: bool
    json: dict[str, Any]


def query_api(
    url: str,
    method: str = "get",
    *,
    headers: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: int = REQUESTS_TIMEOUT,
) -> Response:
    req_headers: dict[str, Any] = {}

    req_headers.update(  # pyright: ignore[reportUnknownMemberType]
        headers if headers else {}
    )
    func = {
        "GET": requests.get,
        "POST": requests.post,
        "PATCH": requests.patch,
        "DELETE": requests.delete,
        "PUT": requests.put,
    }.get(method.upper(), requests.get)

    resp = None
    try:
        resp = func(
            url, headers=req_headers, json=payload, params=params, timeout=timeout
        )
        return Response(
            status_code=resp.status_code,
            success=resp.ok,
            json=resp.json() if resp.text and resp.text.strip() else {},
        )
    except (JSONDecodeError, Exception) as exc:
        logger.exception(
            f"unexpected error while making request to {url} : "
            f"{resp.text if resp else exc}"
        )
        return Response(
            status_code=resp.status_code if resp else -1,
            success=resp.ok if resp else False,
            json={},
        )
