#!/usr/bin/env python3

"""Create a report of API keys usage in youtube recipes

    ./report_youtube_api_keys.py

    Configuration file named "report_youtube_api_keys.conf.json" must be placed in
    same folder as script and contain a dictionnary of sha256(api_key) =>
    api_key_display_name
"""

import datetime
import hashlib
import json
import os
import pathlib

import requests
import sqlalchemy as sa
import sqlalchemy.orm as so
from jinja2 import Environment, FileSystemLoader

import db.models as dbm
from db import dbsession


@dbsession
def report_youtube_api_keys(session: so.Session, *, display_unknown_secrets=False):
    jinja_env = Environment(loader=FileSystemLoader("./"), autoescape=True)
    jinja_template = jinja_env.get_template("report_youtube_api_keys.txt")
    github_repo = os.environ["GITHUB_REPO"]
    github_token = os.environ["GITHUB_TOKEN"]
    github_issue_assignees = os.environ.get("GITHUB_ISSUE_ASSIGNEES", "").split(",")
    github_issue_labels = os.environ.get("GITHUB_ISSUE_LABELS", "").split(",")
    create_issue = os.environ.get("CREATE_ISSUE", "false").lower() == "true"

    known_api_keys = json.loads(
        pathlib.Path("report_youtube_api_keys.conf.json").read_text()
    )
    print("Listing schedules")
    stmt = (
        sa.select(dbm.Schedule)
        .where(dbm.Schedule.config["task_name"].astext == "youtube")
        .where(dbm.Schedule.config["flags"]["api-key"].astext.is_not(None))
        .order_by(dbm.Schedule.config["flags"]["api-key"].astext)
    )

    schedules = list(session.execute(stmt).scalars())

    schedules_by_api_key = {}
    for schedule in schedules:
        api_key = schedule.config["flags"]["api-key"]
        hashed_api_key = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        if hashed_api_key not in schedules_by_api_key.keys():
            schedules_by_api_key[hashed_api_key] = {
                "api_key": api_key,
                "key_name": known_api_keys[hashed_api_key]
                if hashed_api_key in known_api_keys
                else "unknown",
                "schedules": [],
            }
        schedules_by_api_key[hashed_api_key]["schedules"].append(schedule.name)

    report_data = {}
    report_data["nb_schedules"] = len(schedules)
    report_data["keys"] = []

    for hashed_api_key, data in schedules_by_api_key.items():
        report_data["keys"].append(
            {
                "name": known_api_keys[hashed_api_key]
                if hashed_api_key in known_api_keys.keys()
                else "unknown",
                "schedules": sorted(data["schedules"]),
            }
        )
        if display_unknown_secrets and hashed_api_key not in known_api_keys.keys():
            print("Unknown key:")
            print(f"API key: {data['api_key']}")

    for hashed_key, key_name in known_api_keys.items():
        if hashed_key not in schedules_by_api_key.keys():
            report_data["keys"].append(
                {
                    "name": key_name,
                    "schedules": [],
                }
            )

    report_data["keys"] = sorted(report_data["keys"], key=lambda apikey: apikey["name"])

    report_data["datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = jinja_template.render(report_data=report_data)

    if create_issue:
        print("Creating Github Issue")
        resp = requests.post(
            url=f"https://api.github.com/repos/{github_repo}/issues",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "title": (
                    "Youtube API Key usage report"
                    f" {datetime.datetime.now().strftime('%b %Y')}"
                ),
                "body": jinja_template.render(report_data=report_data),
                "assignees": github_issue_assignees,
                "labels": github_issue_labels,
            },
        )
        print(resp.json())
        resp.raise_for_status()
        print(f"Github issue created successfully in {github_repo}")

    else:
        print(report)

    return


if __name__ == "__main__":
    report_youtube_api_keys(display_unknown_secrets=False)
    print("DONE.")
