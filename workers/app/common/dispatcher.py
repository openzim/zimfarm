#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import json
import base64
import pathlib
import datetime
import tempfile
import subprocess

import requests

from common.constants import OPENSSL_BIN


def get_token_ssh(webapi_uri, username, private_key):
    """ retrieve access_token, refresh_token using SSH private key as auth

        - build a standard message (username:timestamp in ISO format)
        - sign this message file using private key
        - send message and signature as headers
        - server validates signature and checks timestamp is recent then auths """

    now = datetime.datetime.utcnow()
    message = f"{username}:{now.isoformat()}"

    with tempfile.TemporaryDirectory() as tmp_dirname:
        tmp_dir = pathlib.Path(tmp_dirname)
        message_path = tmp_dir.joinpath("message")
        signatured_path = tmp_dir.joinpath(f"{message_path.name}.sig")
        with open(message_path, "w", encoding="ASCII") as fp:
            fp.write(message)
        pkey_util = subprocess.run(
            [
                OPENSSL_BIN,
                "pkeyutl",
                "-sign",
                "-inkey",
                str(private_key),
                "-in",
                str(message_path),
                "-out",
                signatured_path,
            ]
        )
        if pkey_util.returncode != 0:
            raise IOError("unable to sign authentication payload")

        with open(signatured_path, "rb") as fp:
            b64_signature = base64.b64encode(fp.read())

        req = requests.post(
            url=f"{webapi_uri}/auth/ssh_authorize",
            headers={
                "Content-type": "application/json",
                "X-SSHAuth-Message": message,
                "X-SSHAuth-Signature": b64_signature,
            },
        )
        req.raise_for_status()
        return req.json().get("access_token"), req.json().get("refresh_token")


def query_api(token, method, url, payload=None, params=None, headers={}):
    try:
        headers.update({"Authorization": "Token {}".format(token)})
        req = getattr(requests, method.lower(), "get")(
            url=url, headers=headers, json=payload, params=params
        )
    except Exception as exp:
        return (False, 599, "ConnectionError -- {}".format(exp))

    if req.status_code == requests.codes.NO_CONTENT:
        return True, req.status_code, ""

    try:
        resp = req.json() if req.text else {}
    except json.JSONDecodeError:
        return (
            False,
            req.status_code,
            "ResponseError (not JSON): -- {}".format(req.text),
        )
    except Exception as exp:
        return (
            False,
            req.status_code,
            "ResponseError -- {} -- {}".format(str(exp), req.text),
        )

    if req.status_code in (
        requests.codes.OK,
        requests.codes.CREATED,
        requests.codes.ACCEPTED,
    ):
        return True, req.status_code, resp

    if "error" in resp:
        content = resp["error"]
        if "error_description" in resp:
            content += "\n"
            content += str(resp["error_description"])
    else:
        content = str(resp)

    return (False, req.status_code, content)
