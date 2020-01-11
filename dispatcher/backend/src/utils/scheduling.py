#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime

import pytz
import pymongo
import humanfriendly
from bson.son import SON

from common.enum import TaskStatus
from utils.offliners import command_information_for
from common.mongo import Tasks, Schedules, Workers, RequestedTasks

from common.constants import DEFAULT_SCHEDULE_DURATION

logger = logging.getLogger(__name__)


def get_default_duration():
    return {
        "value": int(DEFAULT_SCHEDULE_DURATION),
        "task": None,
        "on": datetime.datetime.now(tz=pytz.utc),
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


def schedule_everything():

    now = datetime.datetime.now()
    requester = "schedule-script"
    priority = 0
    worker = None

    for schedule in Schedules().find({"enabled": True}, {"name": 1, "config": 1}):
        config = schedule["config"]
        # build and save command-information to config
        config.update(command_information_for(config))

        document = {
            "schedule_name": schedule["name"],
            "status": TaskStatus.requested,
            "timestamp": {TaskStatus.requested: now},
            "events": [{"code": TaskStatus.requested, "timestamp": now}],
            "requested_by": requester,
            "priority": priority,
            "worker": worker,
            "config": config,
        }

        if worker:
            document["worker"] = worker

        logger.debug(RequestedTasks().insert_one(document).inserted_id)


def truncate_schedule():
    RequestedTasks().delete_many({})


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


def get_task_eta(task):
    """ compute task duration (dict), remaining (seconds) and eta (datetime) """
    now = datetime.datetime.now()
    duration = get_duration_for(task["schedule_name"], task["worker"])
    elapsed = now - task["timestamp"]["started"]  # delta
    remaining = max([duration["value"] - elapsed.total_seconds(), 60])  # seconds
    remaining *= 1.005  # .5% margin
    eta = now + datetime.timedelta(seconds=remaining)

    return {"duration": duration, "remaining": remaining, "eta": eta}


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
        {"resources": 1, "offliners": 1, "last_seen": 1},
    )

    # worker is not checked-in
    if worker is None:
        logger.error(f"worker `{worker_name}` not checked-in")
        return None

    # find all requested tasks that this worker can do with its total resources
    #   sorted by priorities
    #   sorted by max durations
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
                {"value": f"$schedule.duration.workers.{worker_name}.value"},
            ]
        },
    }
    duration_value_proj.update(projection)

    tasks_worker_could_do = RequestedTasks().aggregate(
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
            {"$project": extract_schedule_proj,},
            {"$project": duration_value_proj},
            {
                "$sort": SON(
                    [
                        ("priority", pymongo.DESCENDING),
                        ("duration.value", pymongo.DESCENDING,),
                    ]
                )
            },
        ]
    )

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
    logger.debug(f"missing {missing_cpu=}, {missing_memory=}, {missing_disk=}")

    # retrieve list of tasks we are currently running with associated resources
    running_tasks = list(
        Tasks().find(
            {"status": {"$nin": TaskStatus.complete()}, "worker": worker_name},
            {"config.resources": 1, "schedule_name": 1, "timestamp": 1},
        )
    )

    # calculate ETAs of the tasks we are currently running
    for task in running_tasks:
        task.update(get_task_eta(task))

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

    # get the ETA that point in time (ETA of last preventing_tasks)
    if preventing_tasks:
        logger.debug(f"we have {len(preventing_tasks)} tasks blocking out way")
        opening_eta = preventing_tasks[-1]["eta"]
        logger.debug(f"{opening_eta=}")
    else:
        # we should not get there: no preventing task yet we don't have our total
        # resources available? problem.
        logger.error("we have no preventing tasks. oops")
        return None

    # get the number of available seconds from now to that ETA
    available_time = (opening_eta - datetime.datetime.now()).total_seconds()
    logger.debug(
        "we have approx. {} to reclaim resources".format(
            humanfriendly.format_timespan(available_time)
        )
    )

    # loop on task[1+] to find the first task which can fit
    for temp_candidate in tasks_worker_could_do:
        if can_run(temp_candidate, available_resources):
            if temp_candidate["duration"]["value"] <= available_time:
                logger.debug(f"{temp_candidate['schedule_name']} it is!")
                return temp_candidate
            logger.debug(f"{temp_candidate['schedule_name']} would take too long")

    # if none in the loop are possible, return None (worker will wait)
    logger.debug("unable to fit anything, you'll have to wait for task to complete")
    return None
