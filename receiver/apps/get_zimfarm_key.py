#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

"""OpenSSH AuthorizedKeysCommand tool for the Zimfarm API

- launched by sshd on autehtication attempt with two parameters
    - username: username being authenticated (should be `uploader`)
    - fingerprint: the SHA 256 fingerprint of the tested key
- must respond with a list of public keys to authenticate it with
- connects to the Zimfarm API to request a public key from the fingerprint
- requests it to be associated with a user having zim.upload permission
"""

import json
import logging
import os
import sys

import requests

default_environ = {
    "ZIMFARM_WEBAPI": "https://api.farm.openzim.org/v2",
    "ZIMFARM_USERNAME": "uploader",
}

# setup logger on STDERR only as stdout is used to send keys to OpenSSH
logger = logging.getLogger("zimfarm-key")
logger.setLevel(logging.DEBUG)
log_format = "[%(asctime)s] %(levelname)s:%(message)s"
stderr_handler = logging.StreamHandler(sys.stderr)
logger.addHandler(stderr_handler)

# load environment variables from a file as not launch from Docker's CMD/entrypoint
try:
    with open(os.getenv("ENVIRON_FILE", "/etc/environ.json"), "r") as fp:
        environ = json.load(fp)
except Exception as exc:
    logger.error(f"unable to load environ file: {exc}")
    environ = default_environ


def print_keys_for(username, fingerprint):
    # skip requests for unexpected users
    if username != environ["ZIMFARM_USERNAME"]:
        logger.warning(f"refused login for {username}")
        return

    keys = fetch_public_keys_for(username, fingerprint)
    if not keys:
        return

    print("\n".join(keys))


def fetch_public_keys_for(username, fingerprint):
    req = requests.get(
        url=f"{environ['ZIMFARM_WEBAPI']}/users/-/keys/{fingerprint}",
        params={"with_permission": ["zim.upload"]},
    )
    try:
        response = req.json()
    except Exception:
        response = {}

    if req.status_code != requests.codes.OK:
        reason = f"HTTP {req.status_code}."
        if response and "message" in response:
            reason += f" {response['message']}"
        logger.warning(f"failed login attempt using {fingerprint}: {reason}")
        return

    logger.info(
        f"granted login for {response['username']} via {response['type']} key "
        f"{response['name']}"
    )
    return [f"{response['key']}"]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.error(f"Usage: {sys.argv[0]} <username> <fingerprint>")
        sys.exit(1)

    sys.exit(print_keys_for(*sys.argv[1:]))
