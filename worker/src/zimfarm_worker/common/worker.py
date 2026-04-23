# vim: ai ts=4 sts=4 et sw=4 nu

import os
import signal
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

import docker

from zimfarm_worker.common import logger
from zimfarm_worker.common.constants import (
    DOCKER_CLIENT_TIMEOUT,
    DOCKER_SOCKET,
    PRIVATE_KEY,
)
from zimfarm_worker.common.cryptography import (
    generate_auth_message,
    get_public_key_fingerprint,
    load_private_key_from_path,
)
from zimfarm_worker.common.docker import list_containers
from zimfarm_worker.common.requests import Response, query_api


class BaseWorker:
    def __init__(
        self,
        worker_name: str,
        webapi_uris: list[str],
        workdir: Path | str,
    ):
        self.worker_name = worker_name
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
            self.private_key = load_private_key_from_path(PRIVATE_KEY)
        except Exception as exc:
            logger.critical("\tprivate key is not valid RSA")
            logger.exception(exc)
            sys.exit(1)
        else:
            self.fingerprint: str = get_public_key_fingerprint(
                self.private_key.public_key()
            )

            logger.info(f"\tprivate key is available and readable ({self.fingerprint})")

    def check_auth(self):
        for uri in self.webapi_uris:
            logger.info(f"testing authentication with {uri}…")
            response = self.query_api(path="/auth/test", method="GET", webapi_uri=uri)
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
            webapi_uri = next(iter(self.webapi_uris))

        auth_message = generate_auth_message(self.worker_name, self.private_key)

        attempts = 0
        headers = headers or {}
        headers["Authorization"] = (
            f"Bearer {auth_message.worker_name}.{auth_message.timestamp_str}."
            f"{auth_message.signature}"
        )
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
                continue
            else:
                return response

        return Response(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            success=False,
            json={},
        )

    def exit_gracefully(self, *args: Any, **kwargs: Any):
        # to be overridden
        pass
