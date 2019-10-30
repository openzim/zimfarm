#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime

import pytz
from bson import ObjectId

from common.entities import TaskStatus
from common.mongo import Tasks, Schedules

logger = logging.getLogger(__name__)


def task_event_handler(task_id, event, payload):
    """ ventilate event processing to appropriate handler """
    handlers = {
        TaskStatus.reserved: task_reserved_event_handler,
        TaskStatus.started: task_started_event_handler,
        TaskStatus.succeeded: task_suceeded_event_handler,
        TaskStatus.failed: task_failed_event_handler,
        TaskStatus.canceled: task_canceled_event_handler,
        TaskStatus.scraper_started: task_scraper_started_event_handler,
        TaskStatus.scraper_completed: task_scraper_completed_event_handler,
        TaskStatus.scraper_killed: task_scraper_killed_event_handler,
        TaskStatus.created_file: task_created_file_event_handler,
        TaskStatus.uploaded_file: task_uploaded_file_event_handler,
    }
    func = handlers.get(event, handle_others)
    return func(task_id, payload)


def get_timestamp_from_event(event: dict) -> datetime.datetime:
    timestamp = event.get("timestamp")
    if not timestamp:
        return datetime.datetime.now(tz=pytz.utc)
    return datetime.datetime.fromisoformat(timestamp).astimezone(pytz.utc)


def save_event(task_id: ObjectId, code: str, timestamp: datetime.datetime, **kwargs):
    """ save event and its accompagning data to database """

    # insert event and sort by timestamp
    Tasks().update_one(
        {"_id": task_id},
        {
            "$push": {
                "events": {
                    "$each": [{"code": code, "timestamp": timestamp}],
                    "$sort": {"timestamp": 1},
                }
            }
        },
    )

    # update task status, timestamp and other fields
    task_updates = {f"timestamp.{code}": timestamp}
    if "scraper_" not in code:
        task_updates["status"] = code

    def add_to_update_if_present(payload_key, update_key):
        if payload_key in kwargs:
            task_updates[update_key] = kwargs[payload_key]

    add_to_update_if_present("worker", "worker")
    add_to_update_if_present("canceled_by", "canceled_by")
    add_to_update_if_present("command", "container.command")
    add_to_update_if_present("image", "container.image")
    add_to_update_if_present("exit_code", "container.exit_code")
    add_to_update_if_present("stdout", "container.stdout")
    add_to_update_if_present("stderr", "container.stderr")
    add_to_update_if_present("timeout", "container.timeout")
    add_to_update_if_present("log", "container.log")
    add_to_update_if_present("task_name", "debug.task_name")
    add_to_update_if_present("task_args", "debug.task_args")
    add_to_update_if_present("task_kwargs", "debug.task_kwargs")
    add_to_update_if_present("traceback", "debug.traceback")
    add_to_update_if_present("exception", "debug.exception")

    # files are uploaded as there are created ; 2 events:
    # - one on file creation with name, size and status=created
    # - one on file upload complete with name and status=uploaded
    if kwargs.get("file", {}).get("name"):
        # mongo doesn't support `.` in keys (so we replace with Unicode Full Stop)
        fkey = kwargs["file"]["name"].replace(".", "．")
        fstatus = kwargs["file"].get("status")
        if fstatus == "created":
            task_updates[f"files.{fkey}"] = {
                "name": kwargs["file"]["name"],
                "size": kwargs["file"].get("size"),  # missing in uploaded,
                "status": fstatus,
                f"{fstatus}_timestamp": timestamp,
            }
        elif fstatus == "uploaded":
            task_updates[f"files.{fkey}.status"] = fstatus
            task_updates[f"files.{fkey}.{fstatus}_timestamp"] = timestamp

    Tasks().update_one({"_id": task_id}, {"$set": task_updates})

    _update_schedule_most_recent_task_status(task_id)


def _update_schedule_most_recent_task_status(task_id):
    """ update `most_recent_task` value of associated schedule """
    # get schedule and last event
    cursor = Tasks().aggregate(
        [
            {"$match": {"_id": task_id}},
            {
                "$project": {
                    "schedule_id": 1,
                    "last_event": {"$arrayElemAt": ["$events", -1]},
                }
            },
        ]
    )
    tasks = [task for task in cursor]
    task = tasks[0] if tasks else None
    if not task:
        return

    # update schedule most recent task
    schedule_id = task["schedule_id"]
    last_event_code = task["last_event"]["code"]
    last_event_timestamp = task["last_event"]["timestamp"]
    if "container" in last_event_code:
        return

    schedule_updates = {
        "most_recent_task": {
            "_id": task_id,
            "status": last_event_code,
            "updated_at": last_event_timestamp,
        }
    }
    Schedules().update_one({"_id": schedule_id}, {"$set": schedule_updates})


def task_reserved_event_handler(task_id, payload):
    worker = payload.get("worker")
    logger.info(f"Task Reserved: {task_id}, worker={worker}")

    save_event(
        task_id, TaskStatus.reserved, get_timestamp_from_event(payload), worker=worker
    )


def task_started_event_handler(task_id, payload):
    logger.info(f"Task Started: {task_id}")

    save_event(
        task_id, TaskStatus.started, get_timestamp_from_event(payload)
    )


def task_suceeded_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Succeeded: {task_id}, {timestamp}")

    save_event(task_id, TaskStatus.succeeded, timestamp)


def task_failed_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Failed: {task_id}, {timestamp}")

    save_event(
        task_id,
        TaskStatus.failed,
        timestamp,
        exception=payload.get("exception"),
        traceback=payload.get("traceback"),
    )


def task_canceled_event_handler(task_id, payload):
    terminated = payload.get("terminated", False)
    logger.info(f"Task Cancelled: {task_id}, terminated: {terminated}")

    save_event(
        task_id,
        TaskStatus.canceled,
        get_timestamp_from_event(payload),
        canceled_by=payload.get("canceled_by"),
    )


def task_scraper_started_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    image = payload.get("image")
    command = payload.get("command")
    log = payload.get("log")
    logger.info(f"Task Container Started: {task_id}, {command}")

    save_event(
        task_id,
        TaskStatus.scraper_started,
        timestamp,
        image=image,
        command=command,
        log=log,
    )


def task_scraper_completed_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    exit_code = payload.get("exit_code")
    stdout = payload.get("stdout")
    stderr = payload.get("stderr")
    log = payload.get("log")
    logger.info(f"Task Container Finished: {task_id}, {exit_code}")

    save_event(
        task_id,
        TaskStatus.scraper_completed,
        timestamp,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        log=log,
    )


def task_scraper_killed_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    timeout = payload.get("timeout")
    logger.info(f"Task Container Killed: {task_id}, after {timeout}s")

    save_event(task_id, TaskStatus.scraper_killed, timestamp, timeout=timeout)


def task_created_file_event_handler(task_id, payload):
    file = payload.get("file", {})
    file["status"] = "created"
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task created file: {task_id}, {file['name']}, {file['size']}")

    save_event(task_id, TaskStatus.succeeded, timestamp, file=file)


def task_uploaded_file_event_handler(task_id, payload):
    file = {"name": payload.get("filename"), "status": "uploaded"}
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task uploaded file: {task_id}, {file['name']}")

    save_event(task_id, TaskStatus.succeeded, timestamp, file=file)


def handle_others(self, event):
    event_description = str(event)[:100]
    logger.info(f"Other event: {event_description}")
    logger.info(f"Other event, keys: {list(event.keys())}")
