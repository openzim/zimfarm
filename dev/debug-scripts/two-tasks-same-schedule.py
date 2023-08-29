import json
import logging
import os
import random
import string
import subprocess
from pathlib import Path

import requests

API_HOST = "localhost"
API_PORT = "8000"

WORKER_NAME = "worker01"
WORKER_MAIL = "worker01@acme.com"
WORKER_CONFIG = {
    "username": WORKER_NAME,
    "cpu": 3,
    "memory": 1024,
    "disk": 0,
    "offliners": ["youtube", "mwoffliner"],
}

SCHEDULE_DEFINITION = {
    "category": "wikipedia",
    "config": {
        "monitor": False,
        "platform": "wikimedia",
        "flags": {},
        "image": {"name": "openzim/mwoffliner", "tag": "latest"},
        "resources": {"cpu": 3, "memory": 1024, "disk": 0},
        "task_name": "mwoffliner",
        "warehouse_path": "/wikipedia",
    },
    "enabled": False,
    "language": {"code": "fr", "name_en": "French", "name_native": "Français"},
    "name": "wikipedia_fr_all",
    "periodicity": "monthly",
    "tags": ["selection", "full", "top"],
}

SCHEDULE_ACTIVATION_PAYLOAD = {
    "enabled": True,
    "flags": {
        "adminEmail": "bob@acme.com",
        "mwUrl": "https://www.acme.com",
        "outputDirectory": "/output",
    },
}

ADMIN_NAME = "admin"
ADMIN_PASSWORD = "admin"

logging.basicConfig(level=logging.INFO, format="%(name)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tool              ")


class Tool:
    def __init__(self) -> None:
        self.access_tokens = {}
        self.refresh_token = {}
        self.running_tasks = []

    def get_url(self, path):
        return f"http://{API_HOST}:{API_PORT}/v1/{path}"

    def get_token(self, username, password):
        logger.info(f"Login user {username}")
        resp = requests.post(
            url=self.get_url("/auth/authorize"),
            headers={
                "username": username,
                "password": password,
                "Content-type": "application/json",
            },
        )
        resp.raise_for_status()
        json_data = resp.json()
        self.access_tokens[username] = json_data.get("access_token")
        self.refresh_token[username] = json_data.get("refresh_token")

    def get_token_headers(self, username):
        return {
            "Authorization": f"Token {self.access_tokens[username]}",
            "Content-type": "application/json",
        }

    def create_worker_user(self):
        if "worker_password" in self.persisted_data:
            return

        logger.info(f"Creating user for {WORKER_NAME}")
        self.persisted_data["worker_password"] = "".join(
            random.choice(string.ascii_letters + string.digits) for i in range(16)
        )
        resp = requests.post(
            url=self.get_url("users"),
            headers=self.get_token_headers(ADMIN_NAME),
            data=json.dumps(
                {
                    "username": WORKER_NAME,
                    "email": WORKER_MAIL,
                    "password": self.persisted_data["worker_password"],
                    "role": "worker",
                }
            ),
        )
        resp.raise_for_status()
        with open(self.persisted_file, "w") as fp:
            json.dump(self.persisted_data, fp)

    def create_schedule(self):
        resp = requests.get(
            url=self.get_url(f"schedules/{SCHEDULE_DEFINITION['name']}"),
            headers=self.get_token_headers(ADMIN_NAME),
        )

        if resp.status_code != 404 and resp.status_code != 200:
            resp.raise_for_status()

        if resp.status_code == 200:
            logger.info("Deleting existing schedule")

            resp = requests.delete(
                url=self.get_url(f"schedules/{SCHEDULE_DEFINITION['name']}"),
                headers=self.get_token_headers(ADMIN_NAME),
                data=json.dumps(SCHEDULE_DEFINITION),
            )
            resp.raise_for_status()

        logger.info("Creating schedule")
        resp = requests.post(
            url=self.get_url("schedules"),
            headers=self.get_token_headers(ADMIN_NAME),
            data=json.dumps(SCHEDULE_DEFINITION),
        )
        resp.raise_for_status()

    def load_persisted_data(self):
        logger.info("Loading persisted data")
        self.persisted_file = (
            Path(__file__).parent.absolute().joinpath("persisted_data.json")
        )
        if self.persisted_file.exists():
            with open(self.persisted_file) as fp:
                self.persisted_data = json.load(fp)
        else:
            self.persisted_data = {}

    # def set_virtual_time(self):

    def check_in_worker(self):
        logger.info("Check-in worker")
        resp = requests.put(
            url=self.get_url(f"workers/{WORKER_NAME}/check-in"),
            headers=self.get_token_headers(WORKER_NAME),
            data=json.dumps(WORKER_CONFIG),
        )
        resp.raise_for_status()

    def set_virtual_time(self, virtual_time):
        logger.info(f"Time is now {virtual_time}")
        os.environ["DATETIMENOW"] = virtual_time

    def activate_schedule(self):
        resp = requests.get(
            url=self.get_url(f"schedules/{SCHEDULE_DEFINITION['name']}"),
            headers=self.get_token_headers(ADMIN_NAME),
        )
        resp.raise_for_status()

        schedule_data = resp.json()
        if schedule_data["enabled"]:
            return

        logger.info("Activating schedule")
        resp = requests.patch(
            url=self.get_url(f"schedules/{SCHEDULE_DEFINITION['name']}"),
            headers=self.get_token_headers(ADMIN_NAME),
            data=json.dumps(SCHEDULE_ACTIVATION_PAYLOAD),
        )
        resp.raise_for_status()

    def run_periodic_scheduler(self):
        logger.info("Run periodic scheduler")
        subprocess.run(["python", "periodic-scheduler.py"])

    def print_requested_tasks(self):
        resp = requests.get(
            url=self.get_url("requested-tasks"),
            headers=self.get_token_headers(ADMIN_NAME),
        )
        resp.raise_for_status()

        requested_tasks = resp.json().get("items")
        if len(requested_tasks) == 0:
            logger.info("No task requested at the moment")
            return

        logger.info("Requested tasks:")
        for task in requested_tasks:
            logger.info(f"- {task}")

    def delete_orphaned_requested_tasks(self):
        resp = requests.get(
            url=self.get_url("requested-tasks"),
            headers=self.get_token_headers(ADMIN_NAME),
        )
        resp.raise_for_status()

        requested_tasks = resp.json().get("items")
        for task in requested_tasks:
            if task["schedule_name"]:
                continue
            logger.info(f"Deleting orphaned requested_task {task['_id']}")
            resp = requests.delete(
                url=self.get_url(f"requested-tasks/{task['_id']}"),
                headers=self.get_token_headers(ADMIN_NAME),
            )
            resp.raise_for_status()

    def start_worker_tasks(self, expected_nb_tasks):
        logger.info(f"Looking after task to start by {WORKER_NAME}")
        resp = requests.get(
            url=self.get_url("requested-tasks/worker"),
            headers=self.get_token_headers(WORKER_NAME),
            params={
                "avail_cpu": WORKER_CONFIG["cpu"],
                "avail_memory": WORKER_CONFIG["memory"],
                "avail_disk": WORKER_CONFIG["disk"],
                "worker": WORKER_NAME,
            },
        )
        resp.raise_for_status()

        requested_tasks = resp.json().get("items")
        if len(requested_tasks) != expected_nb_tasks:
            raise Exception(
                f"Unexpect number of tasks returned: {len(requested_tasks)}"
            )
        for task in requested_tasks:
            logger.info(
                f"Worker {WORKER_NAME} is starting task {task['_id']} for schedule"
                f" {task['schedule_name']}"
            )
            resp = requests.post(
                url=self.get_url(f"tasks/{task['_id']}"),
                headers=self.get_token_headers(WORKER_NAME),
                params={
                    "worker_name": WORKER_NAME,
                },
            )
            resp.raise_for_status()
            self.running_tasks.append(task["_id"])

    def update_task_status(self, task_num, status):
        logger.info(
            f"Transitioning task {self.running_tasks[task_num]} status to '{status}'"
        )
        resp = requests.patch(
            url=self.get_url(f"tasks/{self.running_tasks[task_num]}"),
            headers=self.get_token_headers(WORKER_NAME),
            data=json.dumps(
                {
                    "event": status,
                    "payload": {"timestamp": os.environ.get("DATETIMENOW")},
                }
            ),
        )
        resp.raise_for_status()

    def main(self):
        try:
            logger.info("")
            logger.info(
                "### Prepare base objects (access tokens + worker user + object)"
            )

            self.load_persisted_data()  # load persisted data (worker password)

            self.get_token(ADMIN_NAME, ADMIN_PASSWORD)

            self.create_worker_user()

            self.get_token(WORKER_NAME, self.persisted_data["worker_password"])

            logger.info("")
            logger.info("### Create schedule disabled")

            self.create_schedule()

            self.delete_orphaned_requested_tasks()

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info("### Complete schedule configuration and enable it")

            self.activate_schedule()

            self.set_virtual_time("2023-07-01T00:59:00")

            self.check_in_worker()

            self.print_requested_tasks()

            logger.info("")
            logger.info("### Run periodic scheduler with the schedule enabled")

            self.set_virtual_time("2023-07-01T01:00:00")

            self.check_in_worker()

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info("### Run the periodic scheduler again")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info("### Start task0 execution")

            self.set_virtual_time("2023-07-01T01:01:00")

            self.start_worker_tasks(expected_nb_tasks=1)

            self.set_virtual_time("2023-07-01T01:02:00")

            self.update_task_status(task_num=0, status="started")

            self.set_virtual_time("2023-07-01T01:03:00")

            self.update_task_status(task_num=0, status="scraper_started")

            self.set_virtual_time("2023-07-01T01:04:00")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-07-01T01:59:00")

            logger.info("")
            logger.info("### Run periodic scheduler 1 hour after task0 request")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-07-01T02:00:00")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info(
                "### Run periodic scheduler (1 month - 1 day) after task0 request"
            )

            self.set_virtual_time("2023-07-30T23:59:00")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-07-31T00:00:00")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info("### Run periodic scheduler 1 month after task0 request")

            self.set_virtual_time("2023-07-31T23:59:00")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-08-01T00:00:00")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info(
                "### Run periodic scheduler (1 month - few minutes) after task0 start"
            )

            self.set_virtual_time("2023-08-01T00:59:00")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-08-01T01:00:00")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info(
                "### Run periodic scheduler (1 month + some minutes) after task0 start"
            )

            self.set_virtual_time("2023-08-01T01:59:00")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-08-01T02:00:00")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info("### Start task1 execution")

            self.set_virtual_time("2023-08-01T02:01:00")

            self.start_worker_tasks(expected_nb_tasks=1)

            self.set_virtual_time("2023-08-01T02:02:00")

            self.update_task_status(task_num=1, status="started")

            self.set_virtual_time("2023-08-01T02:03:00")

            self.update_task_status(task_num=1, status="scraper_started")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-08-01T02:04:00")

            self.update_task_status(task_num=1, status="scraper_running")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info(
                "### Task update of `scraper_running`: task0 then task1 few seconds"
                " later, just before periodic scheduler runs"
            )

            self.set_virtual_time("2023-08-01T02:59:10")

            self.update_task_status(task_num=0, status="scraper_running")

            self.set_virtual_time("2023-08-01T02:59:20")

            self.update_task_status(task_num=1, status="scraper_running")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

            logger.info("")
            logger.info(
                "### Task update of `scraper_running`: task1 then task0 few seconds"
                " later, just before periodic scheduler runs"
            )

            self.set_virtual_time("2023-08-01T03:59:10")

            self.update_task_status(task_num=1, status="scraper_running")

            self.set_virtual_time("2023-08-01T03:59:20")

            self.update_task_status(task_num=0, status="scraper_running")

            self.run_periodic_scheduler()

            self.print_requested_tasks()

        except requests.HTTPError as ex:
            logger.error(str(ex))
            logger.error(ex.response.content.decode("UTF8"))


if __name__ == "__main__":
    Tool().main()
