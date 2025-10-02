# Creates a CSV report of tasks completed (successfully or not)
# during last month (for 1st to last day of the month)

import csv
import datetime
import os
from pathlib import Path

import requests
from dateutil.relativedelta import relativedelta

# custom values / functions so this script is standalone
REQUESTS_TIMEOUT = 30


def getnow():
    """naive UTC now"""
    return datetime.datetime.now(datetime.UTC)


# url of the zimfarm API to request
url = os.getenv("ZF_URI", "https://api.farm.zimit.kiwix.org/v2")

# prefix of csv file to create: {prefix}{year}-{month}.csv
file_prefix = os.getenv("FILE_PREFIX", "zimfarm_tasks_")

# list of offliners to include
offliners = os.getenv("OFFLINERS", "zimit").split(",")


def get_event_value(events, code, default=None):
    matching_events = [event for event in events if event["code"] == code]
    if matching_events:
        return matching_events[0]["timestamp"]
    elif default:
        return default
    else:
        raise Exception(f"Impossible to find code '{code}' event in events")


def main():
    now = getnow()
    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = start_of_this_month - relativedelta(months=1)

    nb_per_page = 100
    current_page = 0

    last_task_found = False
    with open(
        Path(
            f"{file_prefix}{start_of_last_month.year}-{start_of_last_month.month:02d}"
            ".csv"
        ),
        "w",
    ) as fh:
        csvwriter = csv.writer(fh)
        csvwriter.writerow(["ID", "URL", "Status", "Requested", "Started", "Completed"])
        while not last_task_found:
            response = requests.get(
                f"{url}/tasks/?skip={current_page * nb_per_page}&limit={nb_per_page}"
                "&status=failed&status=canceled&status=succeeded",
                timeout=REQUESTS_TIMEOUT,
            )
            response.raise_for_status()
            items = response.json()["items"]
            for item in items:
                item_last_modification = datetime.datetime.fromisoformat(
                    item["updated_at"]
                )
                if item_last_modification >= start_of_this_month:
                    # task is too recent (it will be pushed to next report), ignore it
                    continue
                if item_last_modification < start_of_last_month:
                    # we found a task which is older than current period, we stop
                    last_task_found = True
                    break

                response = requests.get(
                    f"{url}/tasks/{item['id']}", timeout=REQUESTS_TIMEOUT
                )
                response.raise_for_status()
                task = response.json()
                offliner = task["config"]["offliner"]["offliner_id"]
                if "all" not in offliners and offliner not in offliners:
                    continue
                csvwriter.writerow(
                    [
                        task["id"],
                        task["config"]["offliner"].get("url")
                        or task["config"]["offliner"]["seeds"],
                        task["status"],
                        get_event_value(task["events"], "requested"),
                        get_event_value(task["events"], "started", "-"),
                        get_event_value(task["events"], "succeeded", "-"),
                    ]
                )
            current_page += 1
            fh.flush()


if __name__ == "__main__":
    main()
