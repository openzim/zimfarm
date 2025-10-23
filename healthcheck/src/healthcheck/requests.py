from dataclasses import dataclass
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any

import aiohttp

from healthcheck import logger
from healthcheck.constants import REQUESTS_TIMEOUT


@dataclass
class Response:
    """A response from the webapi"""

    status_code: HTTPStatus
    success: bool
    json: dict[str, Any]


async def query_api(
    url: str,
    method: str = "get",
    *,
    headers: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = REQUESTS_TIMEOUT,
) -> Response:
    req_headers: dict[str, Any] = {}
    req_headers.update(headers if headers else {})

    async with aiohttp.ClientSession() as session:
        method = method.upper()
        async with session.request(
            method=method,
            url=url,
            headers=req_headers,
            json=payload,
            params=params,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            try:
                text = await resp.text()
                json_data: dict[str, Any] = {} if not text else await resp.json()
                return Response(
                    status_code=HTTPStatus(resp.status),
                    success=resp.ok,
                    json=json_data,
                )
            except (JSONDecodeError, Exception):
                logger.exception(
                    "unexpected error while decoding server response: "
                    f"{await resp.text()}"
                )
                raise
