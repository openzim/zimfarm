#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime

import pymongo
from bson.son import SON

from common import getnow
from common.constants import PERIODICITIES
from common.enum import TaskStatus, SchedulePeriodicity
from utils.offliners import command_information_for
from common.mongo import Tasks, Schedules, Workers, RequestedTasks
from common.constants import DEFAULT_SCHEDULE_DURATION

logger = logging.getLogger(__name__)


def get_default_duration():
    return {
        "value": int(DEFAULT_SCHEDULE_DURATION),
        "on": getnow(),
        "worker": None,
        "task": None,
    }


def update_schedule_duration(schedule_name):
    """ set/update the `duration` object of a schedule by looking at its recent tasks

        value is computed with `scraper_completed - started` timestamps """

    schedule_query = {"name": schedule_name}

    # retrieve last tasks that completed the resources intensive part
    query = {
        "schedule_name": schedule_name,
        f"timestamp.{TaskStatus.scraper_completed}": {"$exists": True},
        f"timestamp.{TaskStatus.started}": {"$exists": True},
        "container.exit_code": 0,
    }

    document = {
        "default": get_default_duration(),
    }

    # we have no finished task for this schedule, using default duration
    if Tasks().count_documents(query) == 0:
        document.update({"available": False, "workers": {}})

    # compute duration from last completed tasks
    else:
        tasks = (
            Tasks()
            .find(query, {"timestamp": 1, "worker": 1})
            .sort(f"timestamp.{TaskStatus.scraper_completed}", pymongo.ASCENDING)
        )

        workers = {
            task["worker"]: {
                "worker": task["worker"],
                "task": task["_id"],
                "value": int(
                    (
                        task["timestamp"]["scraper_completed"]
                        - task["timestamp"]["started"]
                    ).total_seconds()
                ),
                "on": task["timestamp"][TaskStatus.scraper_completed],
            }
            for task in tasks
        }
        if workers:
            document.update({"available": True, "workers": workers})

    Schedules().update_one(schedule_query, {"$set": {"duration": document}})


def request_a_schedule(
    schedule_name, requested_by: str, worker: str = None, priority: int = 0
):
    """ created requested_task for schedule_name if possible else None

        enabled=False schedules can't be requested
        schedule can't be requested if already requested on same worker """

    # skip if already requested
    if RequestedTasks().count_documents(
        {"schedule_name": schedule_name, "worker": worker}
    ):
        return None

    schedule = Schedules().find_one(
        {"name": schedule_name, "enabled": True}, {"config": 1}
    )
    # schedule might be disabled
    if not schedule:
        return None

    config = schedule["config"]
    # build and save command-information to config
    config.update(command_information_for(config))

    now = getnow()

    document = {
        "schedule_name": schedule_name,
        "status": TaskStatus.requested,
        "timestamp": {TaskStatus.requested: now},
        "events": [{"code": TaskStatus.requested, "timestamp": now}],
        "requested_by": requested_by,
        "priority": priority,
        "worker": worker,
        "config": config,
    }

    if worker:
        document["worker"] = worker

    rt_id = RequestedTasks().insert_one(document).inserted_id

    document.update({"_id": str(rt_id)})
    return document


def request_tasks_using_schedule():
    """ create requested_tasks based on schedule's periodicity field

        Expected to be ran periodically to compute what needs to be scheduled """

    requester = "period-scheduler"
    priority = 0
    worker = None

    query = {"enabled": True}
    projection = {"name": 1, "config": 1, "most_recent_task": 1}

    for period, period_data in {
        p: PERIODICITIES.get(p) for p in SchedulePeriodicity.all()
    }.items():
        if not period_data:
            continue  # manually has no data

        period_start = getnow() - datetime.timedelta(days=period_data["days"])
        logger.debug(f"requesting for `{period}` schedules (before {period_start})")

        # find non-requested schedules which last run started before our period start
        query["periodicity"] = period
        for schedule in Schedules().find(query, projection):
            # don't bother if the schedule's already requested
            if (
                RequestedTasks().count_documents({"schedule_name": schedule["name"]})
                > 0
            ):
                continue

            if schedule.get("most_recent_task"):
                last_run = Tasks().find_one(
                    {"_id": schedule["most_recent_task"]["_id"]}, {"timestamp": 1}
                )
                # don't bother if it started after this rolling period's start
                if (
                    last_run
                    and last_run["timestamp"].get(
                        "started", datetime.datetime(2019, 1, 1)
                    )
                    > period_start
                ):
                    continue

            if request_a_schedule(schedule["name"], requester, worker, priority):
                logger.debug(f"requested {schedule['name']}")
            else:
                logger.debug(f"could not request {schedule['name']}")


def can_run(task, resources):
    """ whether resources are suffiscient to run this task """
    for key in ["cpu", "memory", "disk"]:
        if task["config"]["resources"][key] > resources[key]:
            return False
    return True


def get_duration_for(schedule_name, worker_name):
    """ duration doc for a schedule and worker (or default one) """
    schedule = Schedules().find_one({"name": schedule_name}, {"duration": 1})
    if not schedule:
        return get_default_duration()
    return schedule["duration"]["workers"].get(
        worker_name, schedule["duration"]["default"]
    )


def get_task_eta(task, worker_name):
    """ compute task duration (dict), remaining (seconds) and eta (datetime) """
    now = getnow()
    duration = get_duration_for(task["schedule_name"], worker_name)
    elapsed = now - task["timestamp"]["started"]  # delta
    remaining = max([duration["value"] - elapsed.total_seconds(), 60])  # seconds
    remaining *= 1.005  # .5% margin
    eta = now + datetime.timedelta(seconds=remaining)

    return {"duration": duration, "remaining": remaining, "eta": eta}


def get_reqs_doable_by(worker):
    """ cursor of RequestedTasks() doable by a worker using all its resources

        - sorted by priority
        - sorted by duration (longest first) """
    query = {}
    for res_key in ("cpu", "memory", "disk"):
        query[f"config.resources.{res_key}"] = {"$lte": worker["resources"][res_key]}
    query["config.task_name"] = {"$in": worker["offliners"]}

    projection = {
        "_id": 1,
        "status": 1,
        "schedule_name": 1,
        "config.task_name": 1,
        "config.resources": 1,
        "timestamp.requested": 1,
        "requested_by": 1,
        "priority": 1,
        "worker": 1,
    }

    # make schedule available directly (lookup returned array)
    extract_schedule_proj = {
        "schedule": {"$arrayElemAt": ["$schedules", 0]},
    }
    extract_schedule_proj.update(projection)
    # add a single int value for duration (real or default) for comparisons
    duration_value_proj = {
        "duration": {
            "$mergeObjects": [
                {"value": "$schedule.duration.default.value"},
                {"value": f"$schedule.duration.workers.{worker['name']}.value"},
            ]
        },
    }
    duration_value_proj.update(projection)

    return RequestedTasks().aggregate(
        [
            {"$match": query},
            # inner join on schedules
            {
                "$lookup": {
                    "from": "schedules",
                    "localField": "schedule_name",
                    "foreignField": "name",
                    "as": "schedules",
                }
            },
            {"$project": extract_schedule_proj},
            {"$project": duration_value_proj},
            {
                "$sort": SON(
                    [
                        ("priority", pymongo.DESCENDING),
                        ("duration.value", pymongo.DESCENDING),
                    ]
                )
            },
        ]
    )


def get_currently_running_tasks(worker_name):
    """ list of tasks being run by worker at this moment, including ETA """
    running_tasks = list(
        Tasks().find(
            {"status": {"$nin": TaskStatus.complete()}, "worker": worker_name},
            {"config.resources": 1, "schedule_name": 1, "timestamp": 1},
        )
    )

    # calculate ETAs of the tasks we are currently running
    for task in running_tasks:
        task.update(get_task_eta(task, worker_name))

    return running_tasks


def get_possible_task_with(tasks_worker_could_do, available_resources, available_time):
    """ first of possible tasks runnable with availresources within avail_time """
    for temp_candidate in tasks_worker_could_do:
        if can_run(temp_candidate, available_resources):
            if temp_candidate["duration"]["value"] <= available_time:
                logger.debug(f"{temp_candidate['schedule_name']} it is!")
                return temp_candidate
            logger.debug(f"{temp_candidate['schedule_name']} would take too long")


def find_requested_task_for(username, worker_name, avail_cpu, avail_memory, avail_disk):
    """ optimal requested_task to run now for a given worker

        Accounts for:
         - longest tasks this worker can do (total resources)
         - available resources now (sent)
         - extimated duration to reclaim resources for longest tasks
    """

    # get total resources for that worker
    worker = Workers().find_one(
        {"username": username, "name": worker_name},
        {"resources": 1, "offliners": 1, "last_seen": 1, "name": 1},
    )

    # worker is not checked-in
    if worker is None:
        logger.error(f"worker `{worker_name}` not checked-in")
        return None

    # find all requested tasks that this worker can do with its total resources
    #   sorted by priorities
    #   sorted by max durations
    tasks_worker_could_do = get_reqs_doable_by(worker)

    # record available resources
    available_resources = {"cpu": avail_cpu, "memory": avail_memory, "disk": avail_disk}

    try:
        # candidate is task[0]
        candidate = next(tasks_worker_could_do)
    except StopIteration:
        logger.debug("nothing scheduled")
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

    # retrieve list of tasks we are currently running with associated resources
    running_tasks = get_currently_running_tasks(worker_name)

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
