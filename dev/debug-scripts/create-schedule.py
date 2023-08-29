import json
import logging

import requests

API_HOST = "localhost"
API_PORT = "8000"

SCHEDULE_DEFINITION = {
    "category": "freecodecamp",
    "config": {
        "monitor": False,
        "platform": None,
        "flags": {},
        "image": {"name": "openzim/freecodecamp", "tag": "1.0.0"},
        "resources": {"cpu": 3, "memory": 1024, "disk": 0},
        "task_name": "freecodecamp",
        "warehouse_path": "/freecodecamp",
    },
    "enabled": False,
    "language": {"code": "fr", "name_en": "French", "name_native": "Français"},
    "name": "fcc_javascript",
    "periodicity": "quarterly",
    "tags": [],
}

SCHEDULE_ACTIVATION_PAYLOAD = {
    "enabled": True,
    "flags": {
        "output-dir": "/output",
        "course": (
            "regular-expressions,basic-javascript,basic-data-structures,debugging,"
            "functional-programming,object-oriented-programming,"
            "basic-algorithm-scripting,intermediate-algorithm-scripting,"
            "javascript-algorithms-and-data-structures-projects"
        ),
        "language": "eng",
        "name": "fcc_en_javascript",
        "title": "freeCodeCamp Javascript",
        "description": "FCC Javascript Courses",
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

    def main(self):
        try:
            logger.info("")
            logger.info("### Prepare base objects (admin access token)")

            self.get_token(ADMIN_NAME, ADMIN_PASSWORD)

            logger.info("")
            logger.info("### Create schedule disabled")

            self.create_schedule()

            logger.info("")
            logger.info("### Complete schedule configuration and enable it")

            self.activate_schedule()

        except requests.HTTPError as ex:
            logger.error(str(ex))
            logger.error(ex.response.content.decode("UTF8"))


if __name__ == "__main__":
    Tool().main()
