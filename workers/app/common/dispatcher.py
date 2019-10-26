#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import json

import requests


def get_token(webapi_uri, username, password):
    req = requests.post(
        url=f"{webapi_uri}/auth/authorize",
        headers={
            "username": username,
            "password": password,
            "Content-type": "application/json",
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
