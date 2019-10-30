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

        - build a standard JSON payload (username, timestamp)
        - sign this payload file using private key
        - send username, payload and signature
        - server validates signature and checks timestamp is recent then auths """

    now = datetime.datetime.now()
    payload = f"{username}:{now.isoformat()}"  # our message

    with tempfile.TemporaryDirectory() as tmp_dirname:
        tmp_dir = pathlib.Path(tmp_dirname)
        payload_path = tmp_dir.joinpath("payload.txt")
        signatured_path = tmp_dir.joinpath(f"{payload_path.name}.sig")
        with open(payload_path, "w", encoding="utf-8") as fp:
            fp.write(payload)
            # json.dump({"username": username, "timestamp": now.isoformat()}, fp)
        pkey_util = subprocess.run(
            [
                OPENSSL_BIN,
                "pkeyutl",
                "-sign",
                "-inkey",
                str(private_key),
                "-in",
                str(payload_path),
                "-out",
                signatured_path,
            ]
        )
        if pkey_util.returncode != 0:
            raise IOError("unable to sign authentication payload")

        with open(signatured_path, "rb") as fp:
            b64_payload_sig = base64.b64encode(fp.read()).decode("ascii")

        req = requests.post(
            url=f"{webapi_uri}/auth/ssh_authorize",
            json={
                "username": username,
                "payload": payload,
                "signed_payload": b64_payload_sig,
            },
            headers={"Content-type": "application/json"},
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

    if req.status_code in (requests.codes.OK, requests.codes.CREATED):
        return True, req.status_code, resp

    return (False, req.status_code, resp["error"] if "error" in resp else str(resp))
