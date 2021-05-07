#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import json
import logging

import requests
import humanfriendly
from marshmallow import ValidationError
from jinja2 import Environment, FileSystemLoader, select_autoescape

from common.mongo import Tasks, RequestedTasks
from utils.json import Encoder
from common.enum import TaskStatus
from common.emailing import send_email_via_mailgun
from common.schemas.models import EventNotificationSchema, ScheduleNotificationSchema
from common.constants import (
    PUBLIC_URL,
    ZIM_DOWNLOAD_URL,
    SLACK_URL,
    SLACK_USERNAME,
    SLACK_EMOJI,
    SLACK_ICON,
)

logger = logging.getLogger(__name__)
jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml", "txt"]),
)
jinja_env.filters["short_id"] = lambda value: str(value)[:5]
jinja_env.filters["format_size"] = lambda value: humanfriendly.format_size(
    value, binary=True
)


class GlobalNotifications:
    methods = EventNotificationSchema().declared_fields.keys()
    events = ScheduleNotificationSchema().declared_fields.keys()
    entries = {}


def load_global_notifications_config():
    """fill-up GlobalNotifications from environ"""
    for event in GlobalNotifications.events:
        event_entry = os.getenv(f"GLOBAL_NOTIFICATION_{event}")
        if not event_entry:
            continue
        entry = {}
        for method_entry in [e.strip() for e in event_entry.split("|")]:
            parts = method_entry.split(",")
            if len(parts) < 2:
                logger.warning(
                    f"Ignoring GLOBAL_NOTIFICATION_{event} registration: malformed"
                )
                continue
            method = parts[0]
            targets = parts[1:]
            if method not in GlobalNotifications.methods:
                logger.warning(
                    f"Ignoring GLOBAL_NOTIFICATION_{event} registration: unknown method"
                )
                continue
            try:
                EventNotificationSchema().load({method: targets})
            except ValidationError as exc:
                logger.warning(
                    f"Ignoring GLOBAL_NOTIFICATION_{event} registration: {exc}"
                )
                continue
            entry.update({method: targets})
        GlobalNotifications.entries.update({event: entry})


def get_context(task):
    return {"base_url": PUBLIC_URL, "download_url": ZIM_DOWNLOAD_URL, "task": task}


def handle_mailgun_notification(task, recipients):
    context = get_context(task)
    subject = jinja_env.get_template("email_subject.txt").render(**context)
    body = jinja_env.get_template("email_body.html").render(**context)
    for recipient in recipients:
        send_email_via_mailgun(recipient, subject, body)


def handle_webhook_notification(task, urls):
    for url in urls:
        try:
            resp = requests.post(url, json=task)
            resp.raise_for_status()
        except Exception as exc:
            logger.error(f"Webhook failed with: {exc}")
            logger.exception(exc)


def handle_slack_notification(task, channels):
    # return early if slack is not configured
    if not SLACK_URL:
        return

    context = get_context(task)
    for channel in channels:
        try:
            requests.post(
                SLACK_URL,
                json={
                    # destination. prefix with # for chans or @ for account
                    "channel": channel,
                    "username": SLACK_USERNAME,
                    "icon_emoji": SLACK_EMOJI,
                    "icon_url": SLACK_ICON,
                    "attachments": [
                        {
                            # desktop notif, mobile, etc
                            "fallback": jinja_env.get_template(
                                "slack_fallback.txt"
                            ).render(**context),
                            "color": {
                                TaskStatus.succeeded: "good",
                                TaskStatus.canceled: "warning",
                                TaskStatus.cancel_requested: "warning",
                                TaskStatus.failed: "danger",
                            }.get(task["status"]),
                            "fields": [
                                {
                                    "title": jinja_env.get_template(
                                        "slack_title.txt"
                                    ).render(**context),
                                    "value": jinja_env.get_template(
                                        "slack_message.txt"
                                    ).render(**context),
                                }
                            ],
                        }
                    ],
                },
            )
        except Exception as exc:
            logger.error(f"Failed to submit slack notification: {exc}")
            logger.exception(exc)


def handle_notification(task_id, event):
    # alias for all complete status
    if event in TaskStatus.complete():
        event = "ended"

    # exit early if not a triggering event
    if event not in GlobalNotifications.events:
        return

    task = Tasks().find_one({"_id": task_id}) or RequestedTasks().find_one(
        {"_id": task_id}
    )
    if not task:
        return

    # serialize/unserialize task so we use a safe version from now-on
    task = json.loads(json.dumps(task, cls=Encoder))
    global_notifs = GlobalNotifications.entries.get(event, {})
    task_notifs = task.get("notification", {}).get(event, {})

    # exit early if we don't have notification requests for the event
    if not global_notifs and not task_notifs:
        return

    for method, recipients in list(task_notifs.items()) + list(global_notifs.items()):
        func = {
            "mailgun": handle_mailgun_notification,
            "webhook": handle_webhook_notification,
            "slack": handle_slack_notification,
        }.get(method)
        if func and recipients:
            func(task, recipients)


# fill-up GlobalNotifications from environ on module load
load_global_notifications_config()
