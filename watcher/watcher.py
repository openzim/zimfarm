#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" Watch StackExchange dump files repository for updates to download/upload all

    StackExchange dump repository, hosted by Archive.org is refreshed twice a year.
    Archive.org's mirrors are all very slow to download from.

    To speed-up sotoki's scrapes, we need to mirror this folder on a faster server.

    This tool runs forever and checks periodically for those dumps on the main server.

    Should there be an update, this tool would (for each file):
    - compute its version as YYYY-MM based on file modification time
    - check whether we have this version in our S3 bucket
    - check whether zimfarm is currently using the current dump and skip in that case
    - check whether there's a pending task for this dump and delete it in that case
    - if we had the same file but for another version, we'd delete it from bucket
    - upload the file to our S3 bucket with a Metadata for the version
    - delete the local file we downloaded
    - schedule matching recipe(s) on the Zimfarm as we now have updated dumps """

import argparse
import concurrent.futures as cf
import datetime
import json
import logging
import multiprocessing
import os
import pathlib
import re
import signal
import subprocess
import sys
import time
import traceback

import humanfriendly
import jwt
import requests
from kiwixstorage import KiwixStorage
from pif import get_public_ip
from xml_to_dict import XMLtoDict

VERSION = "1.0"
DOWNLOAD_URL = os.getenv("DOWNLOAD_URL", "https://archive.org/download/stackexchange")
ZIMFARM_API_URL = os.getenv("ZIMFARM_API_URL", "https://api.farm.openzim.org/v1")
ASCII_LOGO = r"""
  __                                         _       _
 / _| __ _ _ __ _ __ ___      __      ____ _| |_ ___| |__   ___ _ __
| |_ / _` | '__| '_ ` _ \ ____\ \ /\ / / _` | __/ __| '_ \ / _ \ '__|
|  _| (_| | |  | | | | | |_____\ V  V / (_| | || (__| | | |  __/ |
|_|  \__,_|_|  |_| |_| |_|      \_/\_/ \__,_|\__\___|_| |_|\___|_|

"""

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s::%(levelname)s] %(message)s"
)
logger = logging.getLogger("watcher")
# disable boto3's verbose logging
for logger_name in set(["urllib3", "boto3", "botocore", "s3transfer"]):
    logging.getLogger(logger_name).setLevel(logging.WARNING)


def is_running_inside_container():
    """whether running inside a Docker container"""
    fpath = pathlib.Path("/proc/self/cgroup")
    if not fpath.exists():
        return False
    try:
        with open(fpath, "r") as fh:
            for line in fh.readlines():
                if line.strip().rsplit(":", 1)[-1] != "/":
                    return True
    finally:
        pass
    return False


def get_version_for(url):
    """casted datetime of the Last-Modified header for an URL"""
    with requests.head(url, allow_redirects=True) as resp:
        if resp.status_code == 404:
            raise FileNotFoundError(url)
        return datetime.datetime.strptime(
            resp.headers.get("last-modified"), "%a, %d %b %Y %H:%M:%S GMT"
        ).strftime("%Y-%m")


def get_token(api_url, username, password):
    """Access-token, Refresh-token for a pair of Zimfarm credentials"""
    req = requests.post(
        url=f"{api_url}/auth/authorize",
        headers={
            "username": username,
            "password": password,
            "Content-type": "application/json",
        },
    )
    req.raise_for_status()
    return req.json().get("access_token"), req.json().get("refresh_token")


def query_api(token, method, url, payload=None, params=None, headers=None, attempt=0):
    """success, status_code, payload from a query to Zimfamr API"""
    req_headers = {}
    req_headers.update(headers or {})
    try:
        req_headers.update({"Authorization": f"Token {token}"})
        req = getattr(requests, method.lower(), "get")(
            url=url, headers=req_headers, json=payload, params=params
        )
    except Exception as exc:
        attempt += 1
        logger.error(f"ConnectionError (attempt {attempt}) for {method} {url} -- {exc}")
        if attempt <= 3:
            time.sleep(attempt * 60 * 2)
            return query_api(token, method, url, payload, params, headers, attempt)
        return (False, 599, f"ConnectionError -- {exc}")

    if req.status_code == requests.codes.NO_CONTENT:
        return True, req.status_code, ""

    try:
        resp = req.json() if req.text else {}
    except json.JSONDecodeError:
        return (
            False,
            req.status_code,
            f"ResponseError (not JSON): -- {req.text}",
        )
    except Exception as exc:
        return (
            False,
            req.status_code,
            f"ResponseError -- {exc} -- {req.text}",
        )

    if req.status_code in (
        requests.codes.OK,
        requests.codes.CREATED,
        requests.codes.ACCEPTED,
    ):
        return True, req.status_code, resp

    if "error" in resp:
        content = resp["error"]
        if "error_description" in resp:
            content += "\n"
            content += str(resp["error_description"])
    else:
        content = str(resp)

    return (False, req.status_code, content)


class WatcherRunner:
    def __init__(self, **kwargs):
        self.running = True

        # registering exit signals
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGQUIT, self.exit_gracefully)

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def work_dir(self):
        return self._work_dir

    @work_dir.setter
    def work_dir(self, value):
        self._work_dir = pathlib.Path(value).expanduser()
        self._work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def duration(self):
        return datetime.timedelta(seconds=self._duration)

    @duration.setter
    def duration(self, value, *args):
        self._duration = humanfriendly.parse_timespan(value)

    def s3_credentials_ok(self):
        logger.info("Testing S3 credentials")
        self.s3_storage = KiwixStorage(self.s3_url_with_credentials)
        if not self.s3_storage.check_credentials(
            list_buckets=True, bucket=True, write=True, read=True, failsafe=True
        ):
            logger.error("S3 cache connection error testing permissions.")
            logger.error(f"  Server: {self.s3_storage.url.netloc}")
            logger.error(f"  Bucket: {self.s3_storage.bucket_name}")
            logger.error(f"  Key ID: {self.s3_storage.params.get('keyid')}")
            logger.error(f"  Public IP: {get_public_ip()}")
            return False
        return True

    def authenticate(self, force=False):
        """authenticate to the Zimfarm API"""
        # our access token should grant us access for 60mn
        if force or self.authentication_expires_on <= datetime.datetime.now():
            try:
                self.access_token, self.refresh_token = get_token(
                    ZIMFARM_API_URL, self.zimfarm_username, self.zimfarm_password
                )
                self.token_payload = jwt.decode(
                    self.access_token,
                    algorithms=["HS256"],
                    options={"verify_signature": False},
                )
                self.authenticated_on = datetime.datetime.now()
                self.authentication_expires_on = datetime.datetime.fromtimestamp(
                    self.token_payload["exp"]
                )
                return True
            except Exception as exc:
                logger.error(f"authenticate() failure: {exc}")
                logger.exception(exc)
                return False
        return True

    def query_api(self, method, path, payload=None, params=None, headers=None):
        """success, status_code, response for a query to Zimfarm API"""
        if not self.authenticate():
            return (False, 0, "")

        attempts = 0
        while attempts <= 1:
            success, status_code, response = query_api(
                self.access_token,
                method,
                f"{ZIMFARM_API_URL}{path}",
                payload,
                params,
                headers or {},
            )
            attempts += 1

            # Unauthorised error: attempt to re-auth as scheduler might have restarted?
            if status_code == requests.codes.UNAUTHORIZED:
                self.authenticate(force=True)
                continue
            else:
                break

        return success, status_code, response

    def zimfarm_credentials_ok(self):
        logger.info(f"Testing Zimfarm credentials with {ZIMFARM_API_URL}…")
        self.access_token = self.refresh_token = self.token_payload = None
        self.authenticated_on = datetime.datetime(2019, 1, 1)
        self.authentication_expires_on = datetime.datetime(2019, 1, 1)

        success, _, _ = self.query_api("GET", "/auth/test")
        return success

    def retrieve_all_sites(self):
        """version, list of domain names for which there's a dump online"""
        url = f"{DOWNLOAD_URL}/Sites.xml"
        resp = requests.get(url)
        parser = XMLtoDict()
        sites = parser.parse(resp.text).get("sites", {}).get("row", [])
        version = get_version_for(url)

        def _filter(item):
            return item in self.only if self.only else 1

        return version, filter(
            _filter, [re.sub(r"^https?://", "", site.get("@Url", "")) for site in sites]
        )

    def get_recipes_for(self, domain):
        """list of Zimfarm recipes names for a StackExchange domain"""
        success, status, payload = self.query_api(
            "GET",
            "/schedules/",
            params={"category": "stack_exchange", "name": f"{domain}_.+"},
        )
        if not success:
            logger.error(f"Can't get `{domain}` schedules from zimfarm")
            return True

        return [recipe["name"] for recipe in payload.get("items", [])]

    def blocked_by_zimfarm(self, domain):
        """Whether a Zimfarm task is using its file now, preventing removal"""
        prefix = f" [{domain}]"
        logger.info(f"{prefix} Getting recipes depending on it")

        recipes = self.get_recipes_for(domain)
        if not recipes:
            return False

        success, status, payload = self.query_api(
            "GET",
            "/tasks/",
            params={"schedule_name": recipes, "status": ["started", "scraper_started"]},
        )
        if not success:
            logger.error(f"{prefix} Can't get tasks from zimfarm")
            return True

        tasks = payload.get("items", [])
        if not tasks:
            return False

        for task in filter(lambda t: t.get("scraper_started"), tasks):
            started_on = datetime.datetime.fromisoformat(
                re.sub(r"Z$", "", task["scraper_started"])
            )
            if started_on < datetime.datetime.now() - datetime.timedelta(days=1):
                logger.debug(f"{prefix} Zimfarm task #{task['_id']} is blocking it")
                return True

        return False

    def unscheduled_in_zimfarm(self, domain):
        """Whether there was a pending task on Zimfarm that would have used this file

        Should there as been, this would unrequest it."""
        prefix = f" [{domain}]"
        recipes = self.get_recipes_for(domain)
        if not recipes:
            return False

        success, status, payload = self.query_api(
            "GET", "/requested-tasks/", params={"schedule_name": recipes}
        )
        if not success:
            logger.error(f"{prefix} Can't get equested-tasks from zimfarm")
            return False

        tasks = payload.get("items", [])
        if not tasks:
            return False

        for task in tasks:
            self.query_api("DELETE", f"/requested-tasks/{task['_id']}")
            logger.debug(f"{prefix} Zimfarm requested-task #{task['_id']} deleted")

        return True

    def schedule_in_zimfarm(self, domain):
        """Schedule matching recipes in Zimfarm as a new dump was uploaded"""
        recipes = self.get_recipes_for(domain)
        if not recipes:
            return False

        success, status, payload = self.query_api(
            "POST", "/requested-tasks/", payload={"schedule_names": recipes}
        )
        if not success:
            logger.error(f"Failed to schedule {recipes} with HTTP {status}: {payload}")
            return []

        return payload.get("requested")

    def update_file(self, key, schedule_upon_success):
        """Do an all-steps update of that file as we know there's a new one avail."""
        domain = re.sub(r".7z$", "", key)
        prefix = f" [{domain}]"

        if self.blocked_by_zimfarm(domain):
            logger.warning(f"{prefix} Zimfarm is using it. Skipping.")
            return

        if self.unscheduled_in_zimfarm(domain):
            logger.info(f"{prefix} Removed requested task on Zimfarm.")

        if self.s3_storage.has_object(key):
            logger.info(f"{prefix} Removing object in S3")
            obsolete = self.s3_storage.get_object_stat(key).meta.get("version")
            self.s3_storage.delete_object(key)
            logger.info(f"{prefix} Removed object (was version {obsolete})")

        logger.info(f"{prefix} Downloading…")
        url = f"{DOWNLOAD_URL}/{key}"
        fpath = self.work_dir / key
        try:
            version = get_version_for(url)
        except FileNotFoundError:
            logger.error(f"{url} is missing upstream. Skipping.")
            return

        wget = subprocess.run(
            ["/usr/bin/env", "wget", "-O", fpath, url],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if wget.returncode != 0:
            logger.error(f"[{key}] Download failed with exit-code {wget.returncode}")
            logger.error(wget.stdout)
            return
        logger.info(f"{prefix} Download completed")

        logger.info(f"{prefix} Uploading to S3…")
        self.s3_storage.upload_file(fpath=fpath, key=key, meta={"version": version})
        logger.info(f"{prefix} Uploaded")

        fpath.unlink()
        logger.info(f"{prefix} Local file removed")

        if schedule_upon_success:
            logger.info(f"{prefix} Scheduling recipe on Zimfarm")
            scheduled = self.schedule_in_zimfarm(domain)
            if scheduled:
                logger.info(f"{prefix} scheduled: {', '.join(scheduled)}")
            elif scheduled is False:
                logger.info(f"{prefix} no recipe to schedule")
            else:
                logger.warning(f"{prefix} couldn't schedule recipe(s)")

    def check_and_go(self):
        logger.info("Checking StackExchange version…")
        version, domains = self.retrieve_all_sites()
        logger.info(f"Latest online version: {version}. Comparing with S3…")

        self.domains_futures = {}  # future: key
        self.domains_executor = cf.ThreadPoolExecutor(max_workers=self.nb_threads)

        for domain in domains:
            # stackoverflow is a special case in that it's not a single file
            # but multiple ones. We need to run the update for each of them
            if domain == "stackoverflow.com":
                keys = [
                    f"{domain}-{part}.7z"
                    for part in (
                        "Badges",
                        "Comments",
                        "PostHistory",
                        "PostLinks",
                        "Posts",
                        "Tags",
                        "Users",
                        "Votes",
                    )
                ]
            else:
                keys = [f"{domain}.7z"]

            for key in keys:
                if not self.s3_storage.has_object_matching(
                    key, meta={"version": version}
                ):
                    logger.info(f" [+] {key}")

                    # update shall trigger a new recipe schedule on Zimfarm upon compl.
                    # - unless requested not to
                    # - unless this is for stackoverflow as this one requires multiple
                    # files and we'd trigger it only on the ~last one.
                    schedule_upon_success = self.schedule_on_update and (
                        domain != "stackoverflow.com" or key.endwsith("-Votes.7z")
                    )
                    future = self.domains_executor.submit(
                        self.update_file,
                        key=key,
                        schedule_upon_success=schedule_upon_success,
                    )
                    self.domains_futures.update({future: key})

        if not self.domains_futures:
            logger.info("All synced up.")

        result = cf.wait(self.domains_futures.keys(), return_when=cf.FIRST_EXCEPTION)
        self.domains_executor.shutdown()

        for future in result.done:
            exc = future.exception()
            if exc:
                key = self.domains_futures.get(future)
                logger.error(f"Error processing {key}: {exc}")
                traceback.print_exception(exc)

        if result.not_done:
            logger.error(
                "Got some not_done files: \n - "
                + "\n - ".join(
                    [self.domains_futures.get(future) for future in result.not_done]
                )
            )

        logger.info("Done.")
        return not result.not_done

    def run(self):
        logger.info(ASCII_LOGO)

        if self.s3_url_with_credentials and not self.s3_credentials_ok():
            raise ValueError("Unable to connect to Optimization Cache. Check its URL.")

        if not self.zimfarm_credentials_ok():
            raise ValueError("Unable to connect to Zimfarm. Check credentials.")

        logger.info(
            f"Starting watcher:\n"
            f"  with zimfarm username: {self.zimfarm_username}\n"
            f"  using cache: {self.s3_storage.url.netloc}\n"
            f"  with bucket: {self.s3_storage.bucket_name}"
            + ("\n  only for:\n   - " + "\n   - ".join(self.only) if self.only else "")
        )

        checked_on = datetime.datetime.now()
        self.check_and_go()
        while self.running:
            if datetime.datetime.now() > checked_on + self.duration:
                checked_on = datetime.datetime.now()
                self.check_and_go()
            time.sleep(5)  # check time every 5s

    def exit_gracefully(self, signum, frame):
        signame = signal.strsignal(signum)
        self.running = False
        logger.info(f"received exit signal ({signame}).")
        sys.exit(1)


def entrypoint():
    parser = argparse.ArgumentParser(
        prog="watcher",
        description="StackExchange dumps watcher/downloader",
    )
    parser.add_argument(
        "--s3",
        help="S3 URL with credentials to upload dumps to.",
        dest="s3_url_with_credentials",
        default=os.getenv("S3_URL"),
        required=not os.getenv("S3_URL"),
    )

    parser.add_argument(
        "--zimfarm-username",
        help="Zimfarm API username. Defaults to ZIMFARM_USERNAME environ",
        dest="zimfarm_username",
        default=os.getenv("ZIMFARM_USERNAME"),
        required=not os.getenv("ZIMFARM_USERNAME"),
    )
    parser.add_argument(
        "--zimfarm-password",
        help="Zimfarm API. Defaults to ZIMFARM_PASSWORD environ",
        dest="zimfarm_password",
        default=os.getenv("ZIMFARM_PASSWORD"),
        required=not os.getenv("ZIMFARM_PASSWORD"),
    )
    parser.add_argument(
        "--dont-schedule-on-update",
        help="Whether to schedule matching Zimfarm recipes on successful dump update",
        dest="schedule_on_update",
        action="store_false",
        default=True,
    )

    parser.add_argument(
        "--every", help="How often to check for updates", default="1d", dest="duration"
    )
    parser.add_argument(
        "--threads",
        help="How many threads to run to parallelize download/upload? "
        "Defaults to 1 inside Docker as we can't guess available CPUs",
        dest="nb_threads",
        type=int,
        default=(
            1 if is_running_inside_container() else multiprocessing.cpu_count() - 1 or 1
        ),
    )

    parser.add_argument(
        "--dir",
        help="Directory to download files into until uploaded",
        dest="work_dir",
        default=os.path.join(os.getcwd(), "output"),
    )

    parser.add_argument(
        "--only",
        help="List of domains to update. For debugging purposes",
        action="append",
    )
    parser.add_argument(
        "--debug", help="Enable verbose output", action="store_true", default=False
    )

    parser.add_argument(
        "--version",
        help="Display version and exit",
        action="version",
        version=VERSION,
    )

    runner = WatcherRunner(**dict(parser.parse_args()._get_kwargs()))

    try:
        sys.exit(runner.run())
    except Exception as exc:
        logger.error(f"FAILED. An error occurred: {exc}")
        if runner.debug:
            logger.exception(exc)
        raise SystemExit(1)


if __name__ == "__main__":
    entrypoint()
