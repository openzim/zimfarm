#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
from collections.abc import Sequence
from pathlib import Path

import requests
from werkzeug.datastructures import MultiDict

from zimfarm_backend.common.constants import (
    MAILGUN_API_KEY,
    MAILGUN_API_URL,
    MAILGUN_FROM,
    REQ_TIMEOUT_NOTIFICATIONS,
)

logger = logging.getLogger(__name__)


def send_email_via_mailgun(
    to: Sequence[str],
    subject: str,
    contents: str,
    cc: Sequence[str] | None = None,
    bcc: Sequence[str] | None = None,
    attachments: Sequence[Path] | None = None,
):
    if not MAILGUN_API_URL or not MAILGUN_API_KEY:
        return

    values = [
        ("from", MAILGUN_FROM),
        ("subject", subject),
        ("html", contents),
    ]
    values += [
        ("to", value) for value in (to if isinstance(to, list | tuple) else [to])
    ]
    values += [
        ("cc", value) for value in (cc if isinstance(cc, list | tuple) else [cc])
    ]
    values += [
        ("bcc", value) for value in (bcc if isinstance(bcc, list | tuple) else [bcc])
    ]
    data = MultiDict(values)

    try:
        resp = requests.post(
            url=f"{MAILGUN_API_URL}/messages",
            auth=("api", MAILGUN_API_KEY),
            data=data,
            files=(
                [
                    ("attachment", (fpath.name, fpath.read_bytes()))
                    for fpath in attachments
                ]
                if attachments
                else []
            ),
            timeout=REQ_TIMEOUT_NOTIFICATIONS,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.error(f"Failed to send mailgun notif: {exc}")
        logger.exception(exc)
    else:
        return resp.json().get("id")
