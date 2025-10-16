import datetime
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

import requests

from zimfarm_worker.common import logger
from zimfarm_worker.common.cryptography import AuthMessage


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


def get_token(
    webapi_uri: str,
    auth_message: AuthMessage,
) -> Token:
    """Get a token from the webapi"""
    request = requests.post(
        f"{webapi_uri}/auth/ssh-authorize",
        headers={
            "X-SSHAuth-Message": auth_message.body,
            "X-SSHAuth-Signature": auth_message.signature,
        },
        timeout=30,
    )
    request.raise_for_status()
    data = request.json()
    return Token(
        access_token=data["access_token"],
        expires_time=datetime.datetime.fromisoformat(data["expires_time"]),
        refresh_token=data["refresh_token"],
        token_type=data["token_type"],
    )


def query_api(
    url: str,
    method: str = "get",
    *,
    headers: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
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

    resp = func(url, headers=req_headers, json=payload, params=params)
    try:
        return Response(
            status_code=resp.status_code,
            success=resp.ok,
            json=resp.json() if resp.text else {},
        )
    except (JSONDecodeError, Exception):
        logger.exception(
            f"unexpected error while decoding server response: {resp.text}"
        )
        raise
