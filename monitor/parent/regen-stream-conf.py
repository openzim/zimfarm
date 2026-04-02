#!/usr/bin/env python3

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import base64
import urllib.request
import uuid
from http import HTTPStatus
from typing import Any, Tuple, Union

API_URL = os.getenv("ZIMFARM_API_URL")
if not API_URL:
    raise OSError("Please set the ZIMFARM_API_URL environment variable")

# Authentication mode: can be either "local" or "oauth"
AUTH_MODE = os.getenv("AUTH_MODE", "local")
ZIMFARM_USERNAME = os.getenv("ZIMFARM_USERNAME", "")
ZIMFARM_PASSWORD = os.getenv("ZIMFARM_PASSWORD", "")
ZIMFARM_OAUTH_ISSUER = os.getenv("ZIMFARM_OAUTH_ISSUER", "https://ory.login.kiwix.org")
ZIMFARM_OAUTH_CLIENT_ID = os.getenv("ZIMFARM_OAUTH_CLIENT_ID", "")
ZIMFARM_OAUTH_CLIENT_SECRET = os.getenv("ZIMFARM_OAUTH_CLIENT_SECRET", "")
ZIMFARM_OAUTH_AUDIENCE_ID = os.getenv("ZIMFARM_OAUTH_AUDIENCE_ID", "")

TEMPLATE = """[__KEY__]
 enabled = yes
 retention = 30d
 db = dbengine
 health enabled = auto
 timeout seconds = 60
 buffer size = 1048576
 reconnect delay = 5
 initial clock resync iterations = 60
 multiple connections = allow
 allow from = *

"""


def format_key(fingerprint: str) -> str:
    """UUID-hex looking from fingerprint"""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, fingerprint)).upper()


class ClientTokenProvider:
    """Client to generate access tokens to authenticate with Zimfarm"""

    def __init__(self):
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    def _generate_oauth_access_token(self) -> None:
        """Generate oauth access token."""

        credentials = f"{ZIMFARM_OAUTH_CLIENT_ID}:{ZIMFARM_OAUTH_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
            "utf-8"
        )

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "python-urllib/3.11",
            "Accept": "application/json",
        }

        payload = {
            "grant_type": "client_credentials",
            "audience": ZIMFARM_OAUTH_AUDIENCE_ID,
        }

        req = urllib.request.Request(
            f"{ZIMFARM_OAUTH_ISSUER}/oauth2/token",
            data=urllib.parse.urlencode(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as response:  # nosec B310
                response_data = json.loads(response.read().decode("utf-8"))
                self._access_token = response_data["access_token"]
        except urllib.error.HTTPError as e:
            raise IOError(
                f"OAuth token generation failed - HTTP Error {e.code}: {e.reason}"
            )

    def _generate_local_access_token(self) -> None:
        """Generate local access token."""
        if self._refresh_token:
            url = f"{API_URL}/auth/refresh"
            payload = {
                "refresh_token": self._refresh_token,
            }
        else:
            url = f"{API_URL}/auth/authorize"
            payload = {
                "username": ZIMFARM_USERNAME,
                "password": ZIMFARM_PASSWORD,
            }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-type": "application/json"}, method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:  # nosec B310
                response_data = json.loads(response.read().decode("utf-8"))
                self._access_token = response_data.get("access_token")
                self._refresh_token = response_data.get("refresh_token")
        except urllib.error.HTTPError as e:
            raise IOError(
                f"Local authentication failed - HTTP Error {e.code}: {e.reason}"
            )

    def get_access_token(self) -> str:
        """Retrieve or generate access token."""
        if self._access_token is None:
            if AUTH_MODE == "oauth":
                self._generate_oauth_access_token()
            elif AUTH_MODE == "local":
                self._generate_local_access_token()
            else:
                raise ValueError(
                    f"Unknown authentication mode: {AUTH_MODE}. "
                    "Allowed values are: 'local', 'oauth'"
                )
        if self._access_token is None:
            raise ValueError("Failed to generate access token.")
        return self._access_token


token_provider = ClientTokenProvider()


def query_api(
    token: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    attempt: int = 0,
) -> Tuple[bool, int, Union[str, dict]]:
    url = f"{API_URL}{path}"

    # Add query parameters to URL if provided
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req_headers = {}
    req_headers.update(headers if headers else {})
    req_headers.update(
        {"Authorization": f"Bearer {token}", "Content-type": "application/json"}
    )

    # Prepare request data
    data = None
    if payload:
        data = json.dumps(payload).encode("utf-8")

    try:
        req = urllib.request.Request(
            url, data=data, headers=req_headers, method=method.upper()
        )
        with urllib.request.urlopen(req) as response:  # nosec B310
            status_code = response.getcode()
            response_text = response.read().decode("utf-8")

            if status_code == HTTPStatus.NO_CONTENT:
                return True, status_code, ""

            try:
                resp = json.loads(response_text) if response_text else {}
            except json.JSONDecodeError:
                return (
                    False,
                    status_code,
                    f"ResponseError (not JSON): -- {response_text}",
                )

            if status_code in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
                return True, status_code, resp

            if "message" in resp:
                content = resp["message"]
            else:
                content = str(resp)

            return (False, status_code, content)

    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            error_body = e.read().decode("utf-8")
            try:
                resp = json.loads(error_body) if error_body else {}
                if "message" in resp:
                    content = resp["message"]
                else:
                    content = str(resp)
            except json.JSONDecodeError:
                content = f"HTTPError: {e.reason} -- {error_body}"
        except Exception:
            content = f"HTTPError: {e.reason}"

        return (False, status_code, content)

    except Exception as exc:
        attempt += 1
        print(f"ConnectionError (attempt {attempt}) for {method} {url} -- {exc}")
        if attempt <= 3:
            time.sleep(attempt * 60 * 2)
            return query_api(token, method, path, payload, params, headers, attempt)
        return (False, 599, f"ConnectionError -- {exc}")


def main() -> None:
    fingerprints = []
    token = token_provider.get_access_token()

    def get_from_api(
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        nonlocal token
        attempts = 0
        success = False
        status_code = 0
        response: Union[str, dict] = ""

        while attempts <= 1:
            success, status_code, response = query_api(
                token, "GET", path, params=params, headers=headers
            )
            attempts += 1

            # Unauthorised error: attempt to re-auth as scheduler might have restarted?
            if status_code == HTTPStatus.UNAUTHORIZED:
                token = token_provider.get_access_token()
                continue
            else:
                break

        if not success:
            raise IOError(f"ERROR HTTP {status_code}: {response}")

        # At this point, we know success is True, so response must be a dict
        assert isinstance(response, dict)
        return response

    for user in get_from_api("/users", params={"limit": 100}).get("items", []):
        if user.get("role") != "worker":
            continue
        for ssh_key in get_from_api(f"/users/{user['username']}").get("ssh_keys", []):
            fingerprints.append(ssh_key.get("fingerprint"))

    content = ""
    for fingerprint in fingerprints:
        key = format_key(fingerprint)
        content += TEMPLATE.replace("__KEY__", key)
    print(content)


if __name__ == "__main__":
    sys.exit(main())
