#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime

from bson import ObjectId

from common import getnow, to_naive_utc
from common.enum import TaskStatus
from common.mongo import Tasks, Schedules
from common.notifications import handle_notification
from common.schemas.models import ScheduleConfigSchema
from common.constants import SECRET_REPLACEMENT
from utils.scheduling import update_schedule_duration

logger = logging.getLogger(__name__)


def task_event_handler(task_id, event, payload):
    """ ventilate event processing to appropriate handler """
    handlers = {
        TaskStatus.reserved: task_reserved_event_handler,
        TaskStatus.started: task_started_event_handler,
        TaskStatus.succeeded: task_suceeded_event_handler,
        TaskStatus.failed: task_failed_event_handler,
        TaskStatus.cancel_requested: task_cancel_requested_event_handler,
        TaskStatus.canceled: task_canceled_event_handler,
        TaskStatus.scraper_started: task_scraper_started_event_handler,
        TaskStatus.scraper_running: task_scraper_running_event_handler,
        TaskStatus.scraper_completed: task_scraper_completed_event_handler,
        TaskStatus.scraper_killed: task_scraper_killed_event_handler,
        TaskStatus.created_file: task_created_file_event_handler,
        TaskStatus.uploaded_file: task_uploaded_file_event_handler,
        TaskStatus.failed_file: task_failed_file_event_handler,
        TaskStatus.checked_file: task_checked_file_event_handler,
        TaskStatus.update: task_update_event_handler,
    }
    func = handlers.get(event, handle_others)
    ret = func(task_id, payload)

    # fire notifications after event has been handled
    handle_notification(task_id, event)

    return ret


def get_timestamp_from_event(event: dict) -> datetime.datetime:
    timestamp = event.get("timestamp")
    if not timestamp:
        return getnow()
    return to_naive_utc(timestamp)


def save_event(task_id: ObjectId, code: str, timestamp: datetime.datetime, **kwargs):
    """ save event and its accompagning data to database """

    task_updates = {}
    # neither file events nor scraper_running should update timestamp list (not unique)
    if code not in TaskStatus.silent_events():
        task_updates[f"timestamp.{code}"] = timestamp
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
    add_to_update_if_present("progress", "container.progress")
    add_to_update_if_present("timeout", "container.timeout")
    add_to_update_if_present("log", "container.log")
    add_to_update_if_present("task_log", "debug.log")
    add_to_update_if_present("task_name", "debug.task_name")
    add_to_update_if_present("task_args", "debug.task_args")
    add_to_update_if_present("task_kwargs", "debug.task_kwargs")
    add_to_update_if_present("traceback", "debug.traceback")
    add_to_update_if_present("exception", "debug.exception")

    # files are uploaded as there are created ; 3 events:
    # - one on file creation with name, size and status=created
    # - one on file upload complete with name and status=uploaded
    # - one on file check complete with result and log
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
        elif fstatus in ("uploaded", "failed"):
            task_updates[f"files.{fkey}.status"] = fstatus
            task_updates[f"files.{fkey}.{fstatus}_timestamp"] = timestamp
        elif fstatus == "checked":
            task_updates[f"files.{fkey}.check_result"] = kwargs["file"].get("result")
            task_updates[f"files.{fkey}.check_log"] = kwargs["file"].get("log")
            task_updates[f"files.{fkey}.check_timestamp"] = timestamp

    Tasks().update_one({"_id": task_id}, {"$set": task_updates})

    _update_schedule_most_recent_task_status(task_id)

    if code == TaskStatus.scraper_completed:
        schedule_name = Tasks().find_one({"_id": task_id}, {"schedule_name": 1})[
            "schedule_name"
        ]
        update_schedule_duration(schedule_name)


def _update_schedule_most_recent_task_status(task_id):
    """ update `most_recent_task` value of associated schedule """
    # get schedule and last event
    cursor = Tasks().aggregate(
        [
            {"$match": {"_id": task_id}},
            {
                "$project": {
                    "schedule_name": 1,
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
    schedule_name = task["schedule_name"]
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
    Schedules().update_one({"name": schedule_name}, {"$set": schedule_updates})


def task_reserved_event_handler(task_id, payload):
    worker = payload.get("worker")
    logger.info(f"Task Reserved: {task_id}, worker={worker}")

    save_event(
        task_id, TaskStatus.reserved, get_timestamp_from_event(payload), worker=worker
    )


def task_started_event_handler(task_id, payload):
    logger.info(f"Task Started: {task_id}")

    save_event(task_id, TaskStatus.started, get_timestamp_from_event(payload))


def task_suceeded_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Succeeded: {task_id}, {timestamp}")

    save_event(task_id, TaskStatus.succeeded, timestamp, task_log=payload.get("log"))


def task_failed_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Failed: {task_id}, {timestamp}")

    save_event(
        task_id,
        TaskStatus.failed,
        timestamp,
        exception=payload.get("exception"),
        traceback=payload.get("traceback"),
        task_log=payload.get("log"),
    )


def task_cancel_requested_event_handler(task_id, payload):
    requested_by = payload.get("canceled_by")
    logger.info(f"Task Cancellation Requested: {task_id}, by: {requested_by}")

    save_event(
        task_id,
        TaskStatus.cancel_requested,
        get_timestamp_from_event(payload),
        canceled_by=requested_by,
    )


def task_canceled_event_handler(task_id, payload):
    logger.info(f"Task Cancelled: {task_id}")

    # if canceled event carries a `canceled_by` and we have none on the task
    # then store it, otherwise keep what's in the task (manual request)
    canceled_by = None
    task = Tasks().find_one({"_id": task_id}, {"canceled_by": 1})
    if payload.get("canceled_by") and task and not task.get("canceled_by"):
        canceled_by = payload.get("canceled_by")

    save_event(
        task_id,
        TaskStatus.canceled,
        get_timestamp_from_event(payload),
        task_log=payload.get("log"),
        canceled_by=canceled_by,
    )


def task_scraper_started_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    image = payload.get("image")
    command = payload.get("command")
    logger.info(f"Task Container Started: {task_id}, {command}")

    save_event(
        task_id,
        TaskStatus.scraper_started,
        timestamp,
        image=image,
        command=command,
    )


def task_scraper_running_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Container ping: {task_id}")

    save_event(
        task_id,
        TaskStatus.scraper_running,
        timestamp,
        stdout=payload.get("stdout"),
        stderr=payload.get("stderr"),
        progress=payload.get("progress"),
    )


def task_scraper_completed_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    exit_code = payload.get("exit_code")
    logger.info(f"Task Container Finished: {task_id}, {exit_code}")

    save_event(
        task_id,
        TaskStatus.scraper_completed,
        timestamp,
        exit_code=exit_code,
        stdout=payload.get("stdout"),
        stderr=payload.get("stderr"),
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

    save_event(task_id, TaskStatus.created_file, timestamp, file=file)


def task_uploaded_file_event_handler(task_id, payload):
    file = {"name": payload.get("filename"), "status": "uploaded"}
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task uploaded file: {task_id}, {file['name']}")

    save_event(task_id, TaskStatus.uploaded_file, timestamp, file=file)


def task_failed_file_event_handler(task_id, payload):
    file = {"name": payload.get("filename"), "status": "failed"}
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task file upload failed: {task_id}, {file['name']}")

    save_event(task_id, TaskStatus.failed_file, timestamp, file=file)


def task_checked_file_event_handler(task_id, payload):
    file = {
        "name": payload.get("filename"),
        "status": "checked",
        "result": payload.get("result"),
        "log": payload.get("log"),
    }
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task checked file: {task_id}, {file['name']}")

    save_event(task_id, TaskStatus.checked_file, timestamp, file=file)


def task_update_event_handler(task_id, payload):
    timestamp = get_timestamp_from_event(payload)
    log = payload.get("log")  # filename / S3 key of text file at upload_uri[logs]
    logger.info(f"Task update: {task_id}, log: {log}")

    save_event(task_id, TaskStatus.update, timestamp, log=log)


def handle_others(self, event):
    event_description = str(event)[:100]
    logger.info(f"Other event: {event_description}")
    logger.info(f"Other event, keys: {list(event.keys())}")


def hide_secret_flags(response):
    if "config" in response:
        offliner = response["config"]["task_name"]
        offliner_schema = ScheduleConfigSchema.get_offliner_schema(offliner)().to_desc()
        secret_fields = [
            flag["data_key"]
            for flag in offliner_schema
            if ("secret" in flag and flag["secret"])
        ]

        for secret_field in secret_fields:
            if secret_field in response["config"]["flags"]:
                index = response["config"]["command"].index(
                    f'--{secret_field}="{response["config"]["flags"][secret_field]}"'
                )
                response["config"]["command"][index] = (
                    "--" + secret_field + "=" + SECRET_REPLACEMENT
                )
                response["config"]["flags"][secret_field] = SECRET_REPLACEMENT
                if "container" in response:
                    response["container"]["command"][index] = (
                        "--" + secret_field + "=" + SECRET_REPLACEMENT
                    )
        response["config"]["str_command"] = " ".join(response["config"]["command"])
