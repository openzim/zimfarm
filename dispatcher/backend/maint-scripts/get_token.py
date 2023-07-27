#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" zimfarm access token from a username and password. Also available via UI.

    export ZF_TOKEN=./get_token.py my-login my-password
"""

import os
import sys

import requests


def get_url(path):
    url = os.getenv("ZF_URI", "https://api.farm.openzim.org/v1")
    return "/".join([url, path[1:] if path[0] == "/" else path])


def get_token_headers(token):
    return {
        "Authorization": "Token {}".format(token),
        "Content-type": "application/json",
    }


def get_token(username, password):
    req = requests.post(
        url=get_url("/auth/authorize"),
        headers={
            "username": username,
            "password": password,
            "Content-type": "application/json",
        },
    )
    req.raise_for_status()
    return req.json().get("access_token"), req.json().get("refresh_token")


def main(username, password):
    access_token, refresh_token = get_token(username, password)
    print(access_token, file=sys.stdout)
    # print("access_token", access_token, file=sys.stderr)
    # print("refresh_token", refresh_token, file=sys.stderr)


if __name__ == "__main__":
    args = sys.argv[1:]
    # print("args", args, file=sys.stderr)
    main(*args)
