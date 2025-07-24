#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import os
import signal
import sys
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any

import docker
import jwt

from common import getnow, logger
from common.constants import (
    DOCKER_CLIENT_TIMEOUT,
    DOCKER_SOCKET,
    PRIVATE_KEY,
)
from common.cryptography import (
    generate_auth_message,
    get_public_key_fingerprint,
    load_private_key_from_path,
)
from common.docker import list_containers
from common.requests import Response, get_token, query_api


@dataclass(kw_only=True)
class JwtUser:
    username: str
    email: str
    scope: dict[str, Any]


@dataclass(kw_only=True)
class JwtPayload:
    iss: str
    exp: float
    iat: float
    subject: str
    user: JwtUser


@dataclass(kw_only=True)
class WebApiConnection:
    uri: str
    access_token: str
    refresh_token: str
    jwt_payload: JwtPayload
    authenticated_on: datetime.datetime
    authentication_expires_on: datetime.datetime


class BaseWorker:
    def __init__(
        self,
        username: str,
        webapi_uris: list[str],
        workdir: Path | str,
    ):
        self.username = username
        self.webapi_uris = webapi_uris
        self.workdir = Path(workdir).resolve()

    def print_config(self, **kwargs: Any):
        # log configuration values
        config_str = "configuration:"
        for key, value in kwargs.items():
            if key == "password":
                continue
            config_str += f"\n\t{key}={value}"
        logger.info(config_str)

    def check_workdir(self):
        logger.info(f"testing workdir at {self.workdir}…")
        if (
            not self.workdir.exists()
            or not self.workdir.is_dir()
            or not os.access(self.workdir, os.W_OK)
        ):
            logger.critical("\tworkdir is not a writable path")
            sys.exit(1)
        else:
            logger.info("\tworkdir is available and writable")

    def check_private_key(self):
        logger.info(f"testing private key at {PRIVATE_KEY}…")
        if (
            not PRIVATE_KEY.exists()
            or not PRIVATE_KEY.is_file()
            or not os.access(PRIVATE_KEY, os.R_OK)
        ):
            logger.critical("\tprivate key is not a readable path")
            sys.exit(1)

        try:
            private_key = load_private_key_from_path(PRIVATE_KEY)
        except Exception as exc:
            logger.critical("\tprivate key is not valid RSA")
            logger.exception(exc)
            sys.exit(1)
        else:
            self.fingerprint: Any = get_public_key_fingerprint(private_key.public_key())

            logger.info(f"\tprivate key is available and readable ({self.fingerprint})")

    def check_auth(self):
        self.connections: dict[str, WebApiConnection] = {
            uri: WebApiConnection(
                uri=uri,
                access_token="",
                refresh_token="",
                jwt_payload=JwtPayload(
                    iss="",
                    exp=0,
                    iat=0,
                    subject="",
                    user=JwtUser(username="", email="", scope={}),
                ),
                authenticated_on=datetime.datetime(2019, 1, 1),
                authentication_expires_on=datetime.datetime(2019, 1, 1),
            )
            for uri in self.webapi_uris
        }

        for uri in self.connections.keys():
            logger.info(f"testing authentication with {uri}…")
            response = self.query_api(
                path=f"{uri}/auth/test",
                method="GET",
            )
            if response.success:
                logger.info("\tauthentication successful")
            else:
                logger.critical("\tauthentication failed.")
                sys.exit(1)

    def check_docker(self):
        logger.info(f"testing docker API on {DOCKER_SOCKET}…")
        if (
            not DOCKER_SOCKET.exists()
            or not DOCKER_SOCKET.is_socket()
            or not os.access(DOCKER_SOCKET, os.R_OK)
        ):
            logger.critical(f"\tsocket ({DOCKER_SOCKET}) not available.")
            sys.exit(1)
        self.docker = docker.DockerClient(
            base_url=f"unix://{DOCKER_SOCKET}", timeout=DOCKER_CLIENT_TIMEOUT
        )
        try:
            if len(list_containers(self.docker)) < 1:
                logger.warning("\tno running container, am I out-of-docker?")
        except Exception as exc:
            logger.critical("\tdocker API access failed: exiting.")
            logger.exception(exc)
            sys.exit(1)
        else:
            logger.info("\tdocker API access successful")

    def register_signals(self):
        logger.info("registering exit signals")
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGQUIT, self.exit_gracefully)

    def authenticate(self, uri: str, *, force: bool = False):
        # our access token should grant us access for 60mn
        if force or self.connections[uri].authentication_expires_on <= getnow():
            try:
                private_key = load_private_key_from_path(PRIVATE_KEY)
                auth_message = generate_auth_message(self.username, private_key)
                token = get_token(uri, auth_message)
                self.connections[uri].access_token = token.access_token
                self.connections[uri].refresh_token = token.refresh_token
                jwt_payload = jwt.decode(
                    self.connections[uri].access_token,
                    algorithms=["HS256"],
                    options={"verify_signature": False},
                )
                self.connections[uri].jwt_payload = JwtPayload(
                    iss=jwt_payload["iss"],
                    exp=jwt_payload["exp"],
                    iat=jwt_payload["iat"],
                    subject=jwt_payload["sub"],
                    user=JwtUser(
                        username=jwt_payload["user"]["username"],
                        email=jwt_payload["user"]["email"],
                        scope=jwt_payload["user"]["scope"],
                    ),
                )
                self.connections[uri].authenticated_on = getnow()
                self.connections[uri].authentication_expires_on = (
                    datetime.datetime.fromtimestamp(
                        self.connections[uri].jwt_payload.exp
                    )
                )
                return True
            except Exception as exc:
                logger.error(f"authenticate() failure: {exc}")
                logger.exception(exc)
                return False
        return True

    def query_api(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        webapi_uri: str | None = None,
    ) -> Response:
        if not webapi_uri:
            webapi_uri = next(iter(self.connections.keys()))

        if not self.authenticate(uri=webapi_uri):
            return Response(
                status_code=HTTPStatus.UNAUTHORIZED,
                success=False,
                json={},
            )

        attempts = 0
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.connections[webapi_uri].access_token}"
        while attempts <= 1:
            response = query_api(
                url=f"{webapi_uri}{path}",
                method=method,
                payload=payload,
                params=params,
                headers=headers,
            )
            attempts += 1

            # Unauthorised error: attempt to re-auth as scheduler might have restarted?
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                self.authenticate(uri=webapi_uri, force=True)
                continue
            else:
                return response

        return Response(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            success=False,
            json={},
        )

    def exit_gracefully(self, *args: Any, **kwargs: Any):
        # to be overriden
        pass
