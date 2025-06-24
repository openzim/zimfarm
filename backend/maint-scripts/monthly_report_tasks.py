# Creates a CSV report of tasks completed (successfully or not)
# during last month (for 1st to last day of the month)

import csv
import datetime
import os
from pathlib import Path

import requests
from dateutil.relativedelta import relativedelta

from zimfarm_backend.common.constants import REQUESTS_TIMEOUT

# url of the zimfarm API to request
url = os.getenv("ZF_URI", "https://api.farm.zimit.kiwix.org/v1")

# prefix of csv file to create: {prefix}{year}-{month}.csv
file_prefix = os.getenv("FILE_PREFIX", "zimfarm_tasks_")

# list of offliners to include
offliners = os.getenv("OFFLINERS", "zimit").split(",")


def main():
    now = datetime.datetime.now(datetime.UTC)
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
                    f"{url}/tasks/{item['_id']}", timeout=REQUESTS_TIMEOUT
                )
                response.raise_for_status()
                task = response.json()
                offliner = task["config"]["task_name"]
                if "all" not in offliners and offliner not in offliners:
                    continue
                csvwriter.writerow(
                    [
                        task["_id"],
                        task["config"]["flags"].get("url")
                        or task["config"]["flags"]["seeds"],
                        task["status"],
                        task["timestamp"]["requested"],
                        task["timestamp"].get("started", "-"),
                        task["updated_at"],
                    ]
                )
            current_page += 1
            fh.flush()


if __name__ == "__main__":
    main()
