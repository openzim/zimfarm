#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

import sqlalchemy.orm as so
from sqlalchemy.orm.attributes import flag_modified

import zimfarm_backend.db.models as dbm
from zimfarm_backend.common import getnow, to_naive_utc
from zimfarm_backend.common.constants import INFORM_CMS
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.external import advertise_book_to_cms
from zimfarm_backend.common.notifications import handle_notification
from zimfarm_backend.errors.http import TaskNotFound, WorkerNotFound
from zimfarm_backend.utils.check import cleanup_value
from zimfarm_backend.utils.scheduling import update_schedule_duration

logger = logging.getLogger(__name__)


def task_event_handler(
    session: so.Session, task_id: UUID, event: str, payload: dict[str, Any]
):
    """ventilate event processing to appropriate handler"""
    handlers: dict[str, Callable[[so.Session, UUID, dict[str, Any]], None]] = {
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
        TaskStatus.requested: task_requested_event_handler,
    }
    func = handlers.get(event, None)
    if func is None:
        handle_others(task_id, event, payload)
        return None
    else:
        ret = func(session, task_id, payload)

    # we need event to be saved in DB before running notifications
    session.flush()

    # fire notifications after event has been handled
    handle_notification(task_id, event, session)

    return ret


def get_timestamp_from_event(event: dict[str, Any]) -> datetime.datetime:
    timestamp = event.get("timestamp")
    if not timestamp:
        return getnow()
    return to_naive_utc(timestamp)


def save_event(
    session: so.Session,
    task_id: UUID,
    code: str,
    timestamp: datetime.datetime,
    **kwargs: Any,
):
    """save event and its accompagning data to database"""

    task = dbm.Task.get(session, task_id, TaskNotFound)
    schedule = task.schedule

    # neither file events nor scraper_running should update timestamp list (not unique)
    if code not in TaskStatus.silent_events():
        # update task status, timestamp and other fields
        task.timestamp[code] = timestamp
        task.events.append({"code": code, "timestamp": timestamp})
        task.status = code
        task.updated_at = timestamp

    def add_to_container_if_present(
        task: dbm.Task, kwargs_key: str, container_key: str
    ) -> None:
        if kwargs_key in kwargs:
            task.container[container_key] = cleanup_value(kwargs[kwargs_key])

    def add_to_debug_if_present(
        task: dbm.Task, kwargs_key: str, debug_key: str
    ) -> None:
        if kwargs_key in kwargs:
            task.debug[debug_key] = cleanup_value(kwargs[kwargs_key])

    if "worker" in kwargs:
        task.worker = dbm.Worker.get(
            session, kwargs["worker"], WorkerNotFound
        )  # pyright: ignore[reportAttributeAccessIssue]
    if "canceled_by" in kwargs:
        task.canceled_by = kwargs["canceled_by"]

    add_to_container_if_present(
        task=task, kwargs_key="command", container_key="command"
    )
    add_to_container_if_present(task=task, kwargs_key="image", container_key="image")
    add_to_container_if_present(
        task=task, kwargs_key="exit_code", container_key="exit_code"
    )
    add_to_container_if_present(task=task, kwargs_key="stdout", container_key="stdout")
    add_to_container_if_present(task=task, kwargs_key="stderr", container_key="stderr")
    add_to_container_if_present(
        task=task, kwargs_key="progress", container_key="progress"
    )
    add_to_container_if_present(task=task, kwargs_key="stats", container_key="stats")
    add_to_container_if_present(
        task=task, kwargs_key="timeout", container_key="timeout"
    )
    add_to_container_if_present(task=task, kwargs_key="log", container_key="log")
    add_to_container_if_present(
        task=task, kwargs_key="artifacts", container_key="artifacts"
    )
    add_to_debug_if_present(task=task, kwargs_key="task_log", debug_key="log")
    add_to_debug_if_present(task=task, kwargs_key="task_name", debug_key="task_name")
    add_to_debug_if_present(task=task, kwargs_key="task_args", debug_key="task_args")
    add_to_debug_if_present(
        task=task, kwargs_key="task_kwargs", debug_key="task_kwargs"
    )
    add_to_debug_if_present(task=task, kwargs_key="traceback", debug_key="traceback")
    add_to_debug_if_present(task=task, kwargs_key="exception", debug_key="exception")

    # files are uploaded as there are created ; 3 events:
    # - one on file creation with name, size and status=created
    # - one on file upload complete with name and status=uploaded
    # - one on file check complete with result and log
    if kwargs.get("file", {}).get("name"):
        fkey = kwargs["file"]["name"]
        fstatus = kwargs["file"].get("status")
        if fstatus == "created":
            task.files[fkey] = {
                "name": kwargs["file"]["name"],
                "size": kwargs["file"].get("size"),  # missing in uploaded,
                "status": fstatus,
                f"{fstatus}_timestamp": timestamp,
            }
        elif fstatus in ("uploaded", "failed"):
            task.files[fkey]["status"] = fstatus
            task.files[fkey][f"{fstatus}_timestamp"] = timestamp
        elif fstatus == "checked":
            task.files[fkey]["check_result"] = kwargs["file"].get("check_result")
            task.files[fkey]["check_log"] = kwargs["file"].get("check_log")
            task.files[fkey]["check_timestamp"] = timestamp
            task.files[fkey]["check_details"] = kwargs["file"].get("check_details")
            task.files[fkey]["info"] = kwargs["file"].get("info")

        flag_modified(task, "files")  # mark 'files' as modified

    session.flush()  # we have to flush first to avoid circular dependency
    if schedule and code == TaskStatus.reserved:
        schedule.most_recent_task = task

    if code == TaskStatus.scraper_completed and schedule:
        update_schedule_duration(session, schedule)


def task_requested_event_handler(
    session: so.Session,  # noqa: ARG001
    task_id: UUID,
    payload: dict[str, Any],  # noqa: ARG001
):
    logger.info(f"Task Requested: {task_id}")


def task_reserved_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    worker = payload.get("worker")
    logger.info(f"Task Reserved: {task_id}, worker={worker}")

    save_event(
        session,
        task_id,
        TaskStatus.reserved,
        get_timestamp_from_event(payload),
        worker=worker,
    )


def task_started_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    logger.info(f"Task Started: {task_id}")

    save_event(session, task_id, TaskStatus.started, get_timestamp_from_event(payload))


def task_suceeded_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Succeeded: {task_id}, {timestamp}")

    save_event(
        session, task_id, TaskStatus.succeeded, timestamp, task_log=payload.get("log")
    )


def task_failed_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Failed: {task_id}, {timestamp}")

    save_event(
        session,
        task_id,
        TaskStatus.failed,
        timestamp,
        exception=payload.get("exception"),
        traceback=payload.get("traceback"),
        task_log=payload.get("log"),
    )


def task_cancel_requested_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    canceled_by = payload.get("canceled_by")
    logger.info(f"Task Cancellation Requested: {task_id}, by: {canceled_by}")

    save_event(
        session,
        task_id,
        TaskStatus.cancel_requested,
        get_timestamp_from_event(payload),
        canceled_by=canceled_by,
    )


def task_canceled_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    logger.info(f"Task Cancelled: {task_id}")

    # if canceled event carries a `canceled_by` and we have none on the task
    # then store it, otherwise keep what's in the task (manual request)
    task = dbm.Task.get(session, task_id, TaskNotFound)
    kwargs = {}
    if not task.canceled_by and payload.get("canceled_by"):
        kwargs["canceled_by"] = payload.get("canceled_by")

    save_event(
        session,
        task_id,
        TaskStatus.canceled,
        get_timestamp_from_event(payload),
        task_log=payload.get("log"),
        **kwargs,
    )


def task_scraper_started_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    timestamp = get_timestamp_from_event(payload)
    image = payload.get("image")
    command = payload.get("command")
    logger.info(f"Task Container Started: {task_id}, {command}")

    save_event(
        session,
        task_id,
        TaskStatus.scraper_started,
        timestamp,
        image=image,
        command=command,
    )


def task_scraper_running_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task Container ping: {task_id}")

    save_event(
        session,
        task_id,
        TaskStatus.scraper_running,
        timestamp,
        stdout=payload.get("stdout"),
        stderr=payload.get("stderr"),
        progress=payload.get("progress"),
        stats=payload.get("stats"),
    )


def task_scraper_completed_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    timestamp = get_timestamp_from_event(payload)
    exit_code = payload.get("exit_code")
    logger.info(f"Task Container Finished: {task_id}, {exit_code}")

    save_event(
        session,
        task_id,
        TaskStatus.scraper_completed,
        timestamp,
        exit_code=exit_code,
        stdout=payload.get("stdout"),
        stderr=payload.get("stderr"),
    )


def task_scraper_killed_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    timestamp = get_timestamp_from_event(payload)
    timeout = payload.get("timeout")
    logger.info(f"Task Container Killed: {task_id}, after {timeout}s")

    save_event(session, task_id, TaskStatus.scraper_killed, timestamp, timeout=timeout)


def task_created_file_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    file = payload.get("file", {})
    file["status"] = "created"
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task created file: {task_id}, {file['name']}, {file['size']}")

    save_event(session, task_id, TaskStatus.created_file, timestamp, file=file)


def task_uploaded_file_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    file = {"name": payload.get("filename"), "status": "uploaded"}
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task uploaded file: {task_id}, {file['name']}")

    save_event(session, task_id, TaskStatus.uploaded_file, timestamp, file=file)


def task_failed_file_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    file = {"name": payload.get("filename"), "status": "failed"}
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task file upload failed: {task_id}, {file['name']}")

    save_event(session, task_id, TaskStatus.failed_file, timestamp, file=file)


def task_checked_file_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    file = {
        "name": payload.get("filename"),
        "status": "checked",
        "check_result": payload.get("result"),
        "check_log": payload.get("log"),
        "check_details": payload.get("details"),
        "info": payload.get("info"),
    }
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task checked file: {task_id}, {file['name']}")

    save_event(session, task_id, TaskStatus.checked_file, timestamp, file=file)

    if INFORM_CMS:
        task = dbm.Task.get(session, task_id, TaskNotFound)
        if filename := file.get("name"):
            advertise_book_to_cms(task, filename)


def task_update_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    timestamp = get_timestamp_from_event(payload)
    if "log" in payload:
        log = payload.get("log")  # filename / S3 key of text file at upload_uri[logs]
        logger.info(f"Task update: {task_id}, log: {log}")
        save_event(session, task_id, TaskStatus.update, timestamp, log=log)

    if "artifacts" in payload:
        artifacts = payload.get(
            "artifacts"
        )  # filename / S3 key of text file at upload_uri[logs]
        logger.info(f"Task update: {task_id}, artifacts: {artifacts}")
        save_event(session, task_id, TaskStatus.update, timestamp, artifacts=artifacts)


def handle_others(task_id: UUID, event: str, payload: dict[str, Any]):
    logger.info(f"Other event: {event}")
    logger.info(f"Other event, task_id: {task_id}")
    logger.info(f"Other event, payload keys: {list(payload.keys())}")
