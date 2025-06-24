#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 nu

"""zimfarm access token from a username and password. Also available via UI.

export ZF_TOKEN=./get_token.py my-login my-password
"""

import os
import sys

import requests

from zimfarm_backend.common.constants import REQUESTS_TIMEOUT


def get_url(path: str) -> str:
    url = os.getenv("ZF_URI", "https://api.farm.openzim.org/v2")
    return "/".join([url, path[1:] if path[0] == "/" else path])


def get_token_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {token}",
        "Content-type": "application/json",
    }


def get_token(username: str, password: str) -> tuple[str, str]:
    req = requests.post(
        url=get_url("/auth/authorize"),
        headers={
            "username": username,
            "password": password,
            "Content-type": "application/json",
        },
        timeout=REQUESTS_TIMEOUT,
    )
    req.raise_for_status()
    return req.json().get("access_token"), req.json().get("refresh_token")


def main(username: str, password: str):
    access_token, _ = get_token(username, password)
    print(access_token)  # noqa: T201


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
