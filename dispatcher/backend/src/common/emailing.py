#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
from typing import Optional, Sequence

import requests
from werkzeug.datastructures import MultiDict

from common.constants import (
    MAILGUN_API_KEY,
    MAILGUN_API_URL,
    MAILGUN_FROM,
    WEB_NOTIFICATIONS_TIMEOUT,
)

logger = logging.getLogger(__name__)


def send_email_via_mailgun(
    to: Sequence[str],
    subject: str,
    contents: str,
    cc: Optional[Sequence] = None,
    bcc: Optional[Sequence] = None,
    headers: Optional[dict] = None,
    attachments: Optional[Sequence] = None,
):
    if not MAILGUN_API_URL or not MAILGUN_API_KEY:
        return

    values = [
        ("from", MAILGUN_FROM),
        ("subject", subject),
        ("html", contents),
    ]
    values += [
        ("to", value) for value in (to if isinstance(to, (list, tuple)) else [to])
    ]
    values += [
        ("cc", value) for value in (cc if isinstance(cc, (list, tuple)) else [cc])
    ]
    values += [
        ("bcc", value) for value in (bcc if isinstance(bcc, (list, tuple)) else [bcc])
    ]
    data = MultiDict(values)

    try:
        resp = requests.post(
            url=f"{MAILGUN_API_URL}/messages",
            auth=("api", MAILGUN_API_KEY),
            data=data,
            files=[
                ("attachment", (fpath.name, open(fpath, "rb").read()))
                for fpath in attachments
            ]
            if attachments
            else [],
            timeout=WEB_NOTIFICATIONS_TIMEOUT,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.error(f"Failed to send mailgun notif: {exc}")
        logger.exception(exc)
    return resp.json().get("id")
