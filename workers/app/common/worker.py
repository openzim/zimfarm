#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import sys
import signal
import pathlib
import datetime
import urllib.parse

import jwt
import docker
import requests

from common import logger
from common.constants import (
    DOCKER_SOCKET,
    PRIVATE_KEY,
    DOCKER_CLIENT_TIMEOUT,
    access_token,
    refresh_token,
    token_payload,
    authenticated_on,
    authentication_expires_on,
)
from common.dispatcher import get_token_ssh, query_api


class BaseWorker:
    def print_config(self, **kwargs):
        # log configuration values
        config_str = "configuration:"
        for key, value in kwargs.items():
            setattr(self, key, value)
            if key == "password":
                continue
            config_str += f"\n\t{key}={value}"
        logger.info(config_str)

    def check_workdir(self):
        self.workdir = pathlib.Path(self.workdir).resolve()
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
        else:
            logger.info("\tprivate key is available and readable")

    def check_auth(self):
        self.connections = {
            webapi_uri: {
                "uri": urllib.parse.urlparse(webapi_uri),
                access_token: None,
                refresh_token: None,
                token_payload: None,
                authenticated_on: datetime.datetime(2019, 1, 1),
                authentication_expires_on: datetime.datetime(2019, 1, 1),
            }
            for webapi_uri in self.webapi_uris
        }

        for webapi_uri in self.connections.keys():
            logger.info(f"testing authentication with {webapi_uri}…")
            success, _, _ = self.query_api("GET", "/auth/test", webapi_uri=webapi_uri)
            if success:
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
            if len(self.docker.containers.list(all=False)) < 1:
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

    def authenticate(self, webapi_uri=None, force=False):
        # our access token should grant us access for 60mn
        if (
            force
            or self.connections[webapi_uri][authentication_expires_on]
            <= datetime.datetime.now()
        ):
            try:
                (
                    self.connections[webapi_uri][access_token],
                    self.connections[webapi_uri][refresh_token],
                ) = get_token_ssh(webapi_uri, self.username, PRIVATE_KEY)
                self.connections[webapi_uri][token_payload] = jwt.decode(
                    self.connections[webapi_uri][access_token],
                    algorithms=["HS256"],
                    options={"verify_signature": False},
                )
                self.connections[webapi_uri][authenticated_on] = datetime.datetime.now()
                self.connections[webapi_uri][
                    authentication_expires_on
                ] = datetime.datetime.fromtimestamp(
                    self.connections[webapi_uri][token_payload]["exp"]
                )
                return True
            except Exception as exc:
                logger.error(f"authenticate() failure: {exc}")
                logger.exception(exc)
                return False
        return True

    def can_stream_logs(self):
        try:
            upload_uri = urllib.parse.urlparse(
                self.task.get("upload", {}).get("logs", {}).get("upload_uri", 1)
            )
        except Exception:
            return False
        return upload_uri.scheme in ("scp", "sftp")

    def query_api(
        self, method, path, payload=None, params=None, headers=None, webapi_uri=None
    ):
        if not webapi_uri:
            webapi_uri = list(self.connections.keys())[0]

        if not self.authenticate(webapi_uri=webapi_uri):
            return (False, 0, "")

        attempts = 0
        while attempts <= 1:
            success, status_code, response = query_api(
                self.connections[webapi_uri][access_token],
                method,
                f"{webapi_uri}{path}",
                payload,
                params,
                headers or {},
            )
            attempts += 1

            # Unauthorised error: attempt to re-auth as scheduler might have restarted?
            if status_code == requests.codes.UNAUTHORIZED:
                self.authenticate(webapi_uri=webapi_uri, force=True)
                continue
            else:
                break

        return success, status_code, response

    def exit_gracefully(self, signum, frame):
        # to be overriden
        pass
