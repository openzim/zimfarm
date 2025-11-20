#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

import sqlalchemy.orm as so
from sqlalchemy import select

from zimfarm_backend.common import getnow, to_naive_utc
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.notifications import handle_notification
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Task
from zimfarm_backend.db.schedule import update_schedule_duration
from zimfarm_backend.db.tasks import create_or_update_task_file
from zimfarm_backend.db.worker import get_worker

logger = logging.getLogger(__name__)


def cleanup_value(value: Any) -> Any:
    """Remove unwanted characters before inserting / updating in DB"""
    if isinstance(value, str):
        return value.replace("\u0000", "")
    return value


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
        TaskStatus.check_results_uploaded: task_check_results_uploaded_event_handler,
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


def handle_file_event(
    session: so.Session,
    task_id: UUID,
    file_data: dict[str, Any],
    timestamp: datetime.datetime,
) -> None:
    """Handle file-related events and update task file records.

    Files are uploaded as they are created; 3 events:
    - one on file creation with name, size and status=created
    - one on file upload complete with name and status=uploaded
    - one on file check complete with result and log
    """
    fstatus = file_data["status"]
    values = FileCreateUpdateSchema(
        name=file_data["name"],
        task_id=task_id,
        status=fstatus,
    )

    if fstatus == "created":
        values.size = file_data.get("size")
        values.created_timestamp = timestamp
    elif fstatus in ("uploaded", "failed"):
        setattr(values, f"{fstatus}_timestamp", timestamp)
    elif fstatus == "checked":
        values.check_result = file_data.get("check_result")
        values.check_timestamp = timestamp
        values.info = file_data.get("info", {})

    elif fstatus == "check_results_uploaded":
        values.check_filename = file_data.get("check_filename")
        values.check_upload_timestamp = timestamp

    create_or_update_task_file(session, values)


def save_event(
    session: so.Session,
    task_id: UUID,
    code: str,
    timestamp: datetime.datetime,
    **kwargs: Any,
):
    """save event and its accompanying data to database"""

    task = session.scalars(select(Task).where(Task.id == task_id)).one_or_none()
    if task is None:
        raise RecordDoesNotExistError(f"Task {task_id} does not exist")
    schedule = task.schedule

    # neither file events nor scraper_running should update timestamp list (not unique)
    if code not in TaskStatus.silent_events():
        # update task status, timestamp and other fields
        task.timestamp.append((code, timestamp))
        task.events.append({"code": code, "timestamp": timestamp})
        task.status = code
        task.updated_at = timestamp

    # For scraper running events, we want to update the updated_at even though it is a
    # silent event. This is because we use it in the periodic-task to determine if
    # a task is "dead" and cancel it.
    if code == TaskStatus.scraper_running:
        task.updated_at = timestamp

    def add_to_container_if_present(
        task: Task, kwargs_key: str, container_key: str
    ) -> None:
        if kwargs_key in kwargs:
            task.container[container_key] = cleanup_value(kwargs[kwargs_key])

    def add_to_debug_if_present(task: Task, kwargs_key: str, debug_key: str) -> None:
        if kwargs_key in kwargs:
            task.debug[debug_key] = cleanup_value(kwargs[kwargs_key])

    if "worker" in kwargs:
        worker = get_worker(session, worker_name=kwargs["worker"])
        task.worker = worker

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

    # Handle file events if present
    if kwargs.get("file"):
        if kwargs.get("file", {}).get("name") and kwargs.get("file", {}).get("status"):
            handle_file_event(session, task.id, kwargs["file"], timestamp)
        else:
            logger.warning(
                f"Invalid file event for task {task.id}, requires at least "
                "'name' and 'status'"
            )

    session.flush()  # we have to flush first to avoid circular dependency
    if schedule and code == TaskStatus.reserved:
        schedule.most_recent_task = task

    if code == TaskStatus.scraper_completed and schedule:
        update_schedule_duration(session, schedule_name=schedule.name)


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
    task = session.get(Task, task_id)
    if task is None:
        raise RecordDoesNotExistError(f"Task {task_id} does not exist")
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
        "info": payload.get("info"),
        "check_result": payload.get("result"),
    }
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task checked file: {task_id}, {file['name']}")

    save_event(session, task_id, TaskStatus.checked_file, timestamp, file=file)


def task_check_results_uploaded_event_handler(
    session: so.Session, task_id: UUID, payload: dict[str, Any]
):
    file = {
        "name": payload.get("filename"),
        "check_filename": payload.get("check_filename"),
        "status": "check_results_uploaded",
    }
    timestamp = get_timestamp_from_event(payload)
    logger.info(f"Task check results uploaded: {task_id}, {file['name']}")

    save_event(
        session, task_id, TaskStatus.check_results_uploaded, timestamp, file=file
    )


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
