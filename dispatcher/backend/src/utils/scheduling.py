#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import functools
import logging
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import insert

import db.models as dbm
from common import getnow
from common.constants import (
    DEFAULT_SCHEDULE_DURATION,
    ENABLED_SCHEDULER,
    LOGS_EXPIRATION,
    LOGS_UPLOAD_URI,
    PERIODICITIES,
    ZIM_EXPIRATION,
    ZIM_UPLOAD_URI,
    ZIMCHECK_OPTION,
)
from common.enum import Platform, SchedulePeriodicity, TaskStatus
from common.schemas.orms import RequestedTaskFullSchema
from db import count_from_stmt, dbsession
from utils.offliners import expanded_config

logger = logging.getLogger(__name__)


def get_default_duration():
    return {
        "value": int(DEFAULT_SCHEDULE_DURATION),
        "on": getnow(),
        "worker": None,
        "task": None,
    }


def update_schedule_duration(session: so.Session, schedule: dbm.Schedule):
    """update the `duration` object of a schedule by looking at its recent tasks

    value is computed with the most recent difference between
    `scraper_completed - started` timestamps"""

    # retrieve tasks that completed the resources intensive part
    # we don't mind to retrieve all of them because they are regularly purged
    tasks = session.execute(
        sa.select(dbm.Task)
        .where(dbm.Task.timestamp.has_key(TaskStatus.started))  # noqa: W601
        .where(dbm.Task.timestamp.has_key(TaskStatus.scraper_completed))
        .where(dbm.Task.container["exit_code"].astext.cast(sa.Integer) == 0)
        .where(dbm.Task.schedule_id == schedule.id)
        .order_by(
            dbm.Task.timestamp[TaskStatus.scraper_completed]["$date"].astext.cast(
                sa.BigInteger
            )
        )
    ).scalars()

    workers_durations = {}
    for task in tasks:
        workers_durations[task.worker_id] = {
            "value": int(
                (
                    task.timestamp[TaskStatus.scraper_completed]
                    - task.timestamp[TaskStatus.started]
                ).total_seconds()
            ),
            "on": task.timestamp[TaskStatus.scraper_completed],
        }

    # compute values that will be inserted (or updated) in the DB
    inserts_durations = [
        {
            "default": False,
            "value": duration_payload["value"],
            "on": duration_payload["on"],
            "schedule_id": schedule.id,
            "worker_id": worker_id,
        }
        for worker_id, duration_payload in workers_durations.items()
    ]

    # let's do an upsert ; conflict on schedule_id + worker_id
    # on conflict, set the on, value, task_id
    upsert_stmt = insert(dbm.ScheduleDuration).values(inserts_durations)
    upsert_stmt = upsert_stmt.on_conflict_do_update(
        index_elements=[
            dbm.ScheduleDuration.schedule_id,
            dbm.ScheduleDuration.worker_id,
        ],
        set_={
            dbm.ScheduleDuration.on: upsert_stmt.excluded.on,
            dbm.ScheduleDuration.value: upsert_stmt.excluded.value,
        },
    )
    session.execute(upsert_stmt)


def request_a_schedule(
    session: so.Session,
    schedule_name: str,
    requested_by: str,
    worker_name: str = None,
    priority: int = 0,
):
    """created requested_task for schedule_name if possible else None

    enabled=False schedules can't be requested
    schedule can't be requested if already requested on same worker"""

    # skip if already requested
    stmt = (
        sa.select(dbm.RequestedTask, dbm.Schedule)
        .join(dbm.Schedule, dbm.RequestedTask.schedule)
        .filter(dbm.Schedule.name == schedule_name)
    )
    if worker_name is not None:
        stmt = stmt.join(dbm.Worker, dbm.RequestedTask.worker).filter(
            dbm.Worker.name == worker_name
        )
    if count_from_stmt(session, stmt):
        return None

    schedule = dbm.Schedule.get(session=session, name=schedule_name, do_checks=False)
    # schedule might be disabled
    if schedule is None or not schedule.enabled:
        return None

    worker = None
    if worker_name is not None:
        worker = dbm.Worker.get(session=session, name=worker_name, do_checks=False)
        # worker might not exist
        if worker is None:
            return None

    config = schedule.config
    # build and save command-information to config
    config = expanded_config(config)

    now = getnow()

    requested_task = dbm.RequestedTask(
        mongo_val=None,
        mongo_id=None,
        status=TaskStatus.requested,
        timestamp={TaskStatus.requested: now},
        events=[{"code": TaskStatus.requested, "timestamp": now}],
        requested_by=requested_by,
        priority=priority,
        config=config,
        upload={
            "zim": {
                "upload_uri": ZIM_UPLOAD_URI,
                "expiration": ZIM_EXPIRATION,
                "zimcheck": ZIMCHECK_OPTION,
            },
            "logs": {
                "upload_uri": LOGS_UPLOAD_URI,
                "expiration": LOGS_EXPIRATION,
            },
        },
        notification=schedule.notification if schedule.notification else {},
        updated_at=now,
    )
    requested_task.schedule = schedule

    if worker:
        requested_task.worker = worker

    session.add(requested_task)
    session.flush()

    requested_task_obj = RequestedTaskFullSchema().dump(requested_task)

    return requested_task_obj


@dbsession
def request_tasks_using_schedule(session: so.Session):
    """create requested_tasks based on schedule's periodicity field

    Expected to be ran periodically to compute what needs to be scheduled"""

    requester = "period-scheduler"
    priority = 0
    worker = None

    for period, period_data in {
        p: PERIODICITIES.get(p) for p in SchedulePeriodicity.all()
    }.items():
        if not period_data:
            continue  # manually has no data

        period_start = getnow() - datetime.timedelta(days=period_data["days"])
        logger.debug(f"requesting for `{period}` schedules (before {period_start})")

        # find non-requested schedules which last run started before our period start
        for schedule in session.execute(
            sa.select(dbm.Schedule)
            .filter(dbm.Schedule.enabled)
            .filter(dbm.Schedule.periodicity == period)
            .filter(
                ~sa.exists().where(dbm.RequestedTask.schedule_id == dbm.Schedule.id)
            )
        ).scalars():
            if schedule.most_recent_task_id is not None:
                last_run = schedule.most_recent_task
                # don't bother if it started after this rolling period's start
                if (
                    last_run
                    and last_run.timestamp.get("started", datetime.datetime(2019, 1, 1))
                    > period_start
                ):
                    continue

            if request_a_schedule(
                session=session,
                schedule_name=schedule.name,
                requested_by=requester,
                worker_name=worker,
                priority=priority,
            ):
                logger.debug(f"requested {schedule.name}")
            else:
                logger.debug(f"could not request {schedule.name}")


def can_run(task, resources):
    """whether resources are suffiscient to run this task"""
    for key in ["cpu", "memory", "disk"]:
        if task["config"]["resources"][key] > resources[key]:
            return False
    return True


def map_duration(duration: dbm.ScheduleDuration):
    return {
        "value": duration.value,
        "on": duration.on,
        "worker": duration.worker.name if duration.worker else None,
    }


def get_duration_for(session, schedule_name, worker_name):
    """duration doc for a schedule and worker (or default one)"""
    schedule = dbm.Schedule.get(session, schedule_name, do_checks=False)
    if schedule is None:
        return get_default_duration()
    return get_duration_for_with_schedule(schedule, worker_name)


def get_duration_for_with_schedule(schedule, worker_name):
    for duration in schedule.durations:
        if duration.worker and duration.worker.name == worker_name:
            return map_duration(duration)
    for duration in schedule.durations:
        if duration.default:
            return map_duration(duration)
    raise Exception(f"No default duration found for schedule {schedule.name}")


def get_task_eta(session, task, worker_name=None):
    """compute task duration (dict), remaining (seconds) and eta (datetime)"""
    now = getnow()
    if not worker_name:
        worker_name = task.get("worker")
    duration = get_duration_for(session, task["schedule_name"], worker_name)
    # delta
    elapsed = now - task["timestamp"].get("started", task["timestamp"]["reserved"])
    remaining = max([duration["value"] - elapsed.total_seconds(), 60])  # seconds
    remaining *= 1.005  # .5% margin
    eta = now + datetime.timedelta(seconds=remaining)

    return {"duration": duration, "remaining": remaining, "eta": eta}


def get_reqs_doable_by(session: so.Session, worker: dbm.Worker) -> List[Dict[str, Any]]:
    """cursor of RequestedTasks() doable by a worker using all its resources

    - sorted by priority
    - sorted by duration (longest first)"""

    def get_document(task: dbm.RequestedTask):
        return {
            "_id": task.id,
            "status": task.status,
            "schedule_name": task.schedule.name,
            "config": {
                "task_name": task.config.get("task_name"),
                "platform": task.config.get("platform"),
                "resources": task.config.get("resources"),
            },
            "timestamp": task.timestamp,
            "requested_by": task.requested_by,
            "priority": task.priority,
            "worker": task.worker.name if task.worker else None,
            "duration": get_duration_for_with_schedule(task.schedule, worker.name),
        }

    stmt = sa.select(dbm.RequestedTask)

    stmt = stmt.filter(
        dbm.RequestedTask.config["resources"]["cpu"].astext.cast(sa.Integer)
        <= worker.cpu
    )
    stmt = stmt.filter(
        dbm.RequestedTask.config["resources"]["memory"].astext.cast(sa.BigInteger)
        <= worker.memory
    )
    stmt = stmt.filter(
        dbm.RequestedTask.config["resources"]["disk"].astext.cast(sa.BigInteger)
        <= worker.disk
    )
    stmt = stmt.filter(
        dbm.RequestedTask.config["task_name"].astext.in_(worker.offliners)
    )

    if worker.selfish:
        stmt = stmt.filter(dbm.RequestedTask.worker_id == worker.id)
    else:
        stmt = stmt.filter(
            sa.or_(
                dbm.RequestedTask.worker_id == worker.id,
                dbm.RequestedTask.worker_id == None,  # noqa: E711
            )
        )

    return list(
        sorted(
            map(get_document, session.execute(stmt).scalars()),
            key=lambda x: (-x["priority"], -x["duration"]["value"]),
        )
    )


def get_currently_running_tasks(
    session: so.Session, worker_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """list of tasks being run by worker at this moment, including ETA"""

    def extract_data(task: dbm.Task):
        return {
            "config": {
                "resources": task.config.get("resources", {}),
                "platform": task.config.get("platform", None),
            },
            "schedule_name": task.schedule.name,
            "timestamp": task.timestamp,
            "worker": task.worker.name,
        }

    stmt = sa.select(dbm.Task).filter(dbm.Task.status.notin_(TaskStatus.complete()))
    if worker_name:
        stmt = stmt.join(dbm.Worker).filter(dbm.Worker.name == worker_name)
    running_tasks = list(map(extract_data, session.execute(stmt).scalars()))

    # calculate ETAs of the tasks we are currently running
    for task in running_tasks:
        task.update(get_task_eta(session, task, worker_name))

    return running_tasks


def get_possible_task_with(tasks_worker_could_do, available_resources, available_time):
    """first of possible tasks runnable with availresources within avail_time"""
    for temp_candidate in tasks_worker_could_do:
        if can_run(temp_candidate, available_resources):
            if temp_candidate["duration"]["value"] <= available_time:
                logger.debug(f"{temp_candidate['schedule_name']} it is!")
                return temp_candidate
            logger.debug(f"{temp_candidate['schedule_name']} would take too long")


def does_platform_allow_worker_to_run(
    worker: dbm.Worker,
    all_running_tasks: List[Dict[str, Any]],
    running_tasks: List[Dict[str, Any]],
    task,
) -> bool:
    """whether worker can now run task according to platform limitations"""
    platform = task["config"].get("platform")
    if not platform:
        return True

    # check whether we have an overall per-platform limit
    platform_overall_limit = Platform.get_max_overall_tasks_for(platform)
    if platform_overall_limit is not None:
        nb_platform_running = sum(
            [
                1
                for running_task in all_running_tasks
                if running_task["config"].get("platform") == platform
            ]
        )
        if nb_platform_running >= platform_overall_limit:
            return False

    # check whether we have a per-worker limit for this platform
    worker_limit = worker.platforms.get(
        platform, Platform.get_max_per_worker_tasks_for(platform)
    )
    if worker_limit is None:
        return True

    nb_worker_running = sum(
        [
            1
            for running_task in running_tasks
            if running_task["config"].get("platform") == platform
        ]
    )
    return nb_worker_running < worker_limit


def find_requested_task_for(
    session: so.Session, username, worker_name, avail_cpu, avail_memory, avail_disk
):
    """optimal requested_task to run now for a given worker

    Accounts for:
     - longest tasks this worker can do (total resources)
     - available resources now (sent)
     - extimated duration to reclaim resources for longest tasks
    """

    # global scheduler switch (for maintainance, mainly)
    if not ENABLED_SCHEDULER:
        return None

    # get total resources for that worker
    worker = session.execute(
        sa.select(dbm.Worker)
        .join(dbm.User)
        .filter(dbm.Worker.name == worker_name)
        .filter(dbm.User.username == username)
    ).scalar_one_or_none()

    # worker is not checked-in
    if worker is None:
        logger.error(f"worker `{worker_name}` not checked-in")
        return None

    # retrieve list of all running tasks with associated resources
    all_running_tasks = get_currently_running_tasks(session)

    # retrieve list of tasks we are currently running with associated resources
    running_tasks = [
        task for task in all_running_tasks if task.get("worker") == worker_name
    ]

    # find all requested tasks that this worker can do with its total resources
    #   sorted by priorities
    #   sorted by max durations
    tasks_worker_could_do = get_reqs_doable_by(session=session, worker=worker)

    # filter-out requested tasks that are not doable now due to platform limitations
    worker_platform_filter = functools.partial(
        does_platform_allow_worker_to_run, worker, all_running_tasks, running_tasks
    )
    tasks_worker_could_do = filter(worker_platform_filter, tasks_worker_could_do)

    # record available resources
    available_resources = {"cpu": avail_cpu, "memory": avail_memory, "disk": avail_disk}

    try:
        # candidate is task[0]
        candidate = next(tasks_worker_could_do)
    except StopIteration:
        logger.debug(f"no request doable by worker (selfish={worker.selfish})")
        return None

    # can worker do task[0] ?
    #   if yes -> return task[0]
    if can_run(candidate, available_resources):
        logger.debug("first candidate can be run!")
        return candidate

    # we don't have enough resources for task[0].

    # find out missing resources
    missing_cpu = max([candidate["config"]["resources"]["cpu"] - avail_cpu, 0])
    missing_memory = max([candidate["config"]["resources"]["memory"] - avail_memory, 0])
    missing_disk = max([candidate["config"]["resources"]["disk"] - avail_disk, 0])
    logger.debug(f"missing cpu:{missing_cpu}, mem:{missing_memory}, dsk:{missing_disk}")

    # pile-up all of those which we need to complete to have enough resources
    preventing_tasks = []
    # sorted by ETA as it's the order in which there're gonna complete
    for task in sorted(running_tasks, key=lambda x: x["eta"]):
        preventing_tasks.append(task)
        if (
            sum([t["config"]["resources"]["cpu"] for t in preventing_tasks])
            >= missing_cpu
            and sum([t["config"]["resources"]["memory"] for t in preventing_tasks])
            >= missing_memory
            and sum([t["config"]["resources"]["disk"] for t in preventing_tasks])
            >= missing_disk
        ):
            # stop when we'd have reclaimed our missing resources
            break

    if not preventing_tasks:
        # we should not get there: no preventing task yet we don't have our total
        # resources available? problem.
        logger.error("we have no preventing tasks. oops")
        return None

    logger.debug(f"we have {len(preventing_tasks)} tasks blocking out way")
    opening_eta = preventing_tasks[-1]["eta"]
    logger.debug(f"opening_eta:{opening_eta}")

    # get the number of available seconds from now to that ETA
    available_time = (opening_eta - getnow()).total_seconds()
    logger.debug(
        "we have approx. {}mn to reclaim resources".format(available_time / 60)
    )

    # loop on task[1+] to find the first task which can fit
    temp_candidate = get_possible_task_with(
        tasks_worker_could_do, available_resources, available_time
    )
    if temp_candidate:
        return temp_candidate

    # if none in the loop are possible, return None (worker will wait)
    logger.debug("unable to fit anything, you'll have to wait for task to complete")
    return None
