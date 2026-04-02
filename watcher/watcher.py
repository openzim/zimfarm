#!/usr/bin/env python

"""Watch StackExchange dump files repository for updates to download/upload all

StackExchange dump repository, hosted by Archive.org is refreshed every quarter.
Archive.org's mirrors are all very slow to download from.

To speed-up sotoki's scrapes, we need to mirror these dumps on a faster server.

This tool runs forever and checks periodically for those dumps on the main server.
Since 2025, it automatically detects the latest dump based on a search query on
Archive.org server.

Then, it retrieves the list of 7z files in the dump, and for each of them:
- ignore sites which are not of interest (ignore all meta websites basically)
- retrieve its `last-modified` value with a HEAD request on Archive.org
- check whether we have this version is in our S3 bucket
- check whether zimfarm is currently using the current dump and skip in that case
- check whether there's a pending task for this dump and delete it in that case
- if we had the same file but for another version, we'd delete it from bucket first
- upload the file to our S3 bucket with a Metadata for the `last-modified` value
- delete the local file we downloaded
- schedule matching and enabled recipe(s) on the Zimfarm when we have updated dump

This tool does not:
- cleanup S3 dumps from deleted StackExchange sites
"""

import argparse
import concurrent.futures as cf
import datetime
import json
import logging
import os
import pathlib
import re
import signal
import subprocess
import sys
import time
import traceback
import urllib.parse
from http import HTTPStatus
from typing import Any, cast

import humanfriendly
import requests
from humanfriendly import parse_timespan
from kiwixstorage import KiwixStorage
from pif import get_public_ip
from requests.auth import HTTPBasicAuth
from xml_to_dict import XMLtoDict

VERSION = "1.0"
DOWNLOAD_URL_BASE = os.getenv("DOWNLOAD_URL_BASE", "https://archive.org/download")
QUERY_URL = os.getenv(
    "QUERY_URL",
    "https://archive.org/services/search/beta/page_production/?user_query=subject:"
    "%22Stack%20Exchange%20Data%20Dump%22%20creator:%22Stack%20Exchange,%20Inc.%22"
    "&hits_per_page=1&page=1&sort=date:desc&aggregations=false"
    "&client_url=https://archive.org/search?query=subject%3A%22"
    "Stack+Exchange+Data+Dump%22+creator%3A%22Stack+Exchange%2C+Inc.%22",
)
ZIMFARM_API_URL = os.getenv("ZIMFARM_API_URL", "https://api.farm.openzim.org/v2")
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

HTTP_REQUEST_TIMEOUT = 30
SUMMARY_FILENAME = "summary.json"

# Authentication mode: can be either "local" or "oauth"
AUTH_MODE = os.getenv("AUTH_MODE", default="local")
ZIMFARM_USERNAME = os.getenv("ZIMFARM_USERNAME", default="")
ZIMFARM_PASSWORD = os.getenv("ZIMFARM_PASSWORD", default="")
ZIMFARM_OAUTH_ISSUER = os.getenv(
    "ZIMFARM_OAUTH_ISSUER", default="https://ory.login.kiwix.org"
)
ZIMFARM_OAUTH_CLIENT_ID = os.getenv("ZIMFARM_OAUTH_CLIENT_ID", default="")
ZIMFARM_OAUTH_CLIENT_SECRET = os.getenv("ZIMFARM_OAUTH_CLIENT_SECRET", default="")
ZIMFARM_OAUTH_AUDIENCE_ID = os.getenv("ZIMFARM_OAUTH_AUDIENCE_ID", default="")
ZIMFARM_TOKEN_RENEWAL_WINDOW = datetime.timedelta(
    seconds=parse_timespan(os.getenv("ZIMFARM_TOKEN_RENEWAL_WINDOW", default="5m"))
)


def getnow():
    """naive UTC now"""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


class ClientTokenProvider:
    """Client to generate access tokens to authenticate with Zimfarm"""

    def __init__(self):
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime.datetime = datetime.datetime.fromtimestamp(
            0
        ).replace(tzinfo=None)

    def _generate_oauth_access_token(self) -> None:
        """Generate oauth access token and update expires_at."""
        response = requests.post(
            f"{ZIMFARM_OAUTH_ISSUER}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "audience": ZIMFARM_OAUTH_AUDIENCE_ID,
            },
            auth=HTTPBasicAuth(ZIMFARM_OAUTH_CLIENT_ID, ZIMFARM_OAUTH_CLIENT_SECRET),
            timeout=HTTP_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        self._access_token = cast(str, payload["access_token"])
        self._expires_at = getnow() + datetime.timedelta(seconds=payload["expires_in"])

    def _generate_local_access_token(self) -> None:
        if self._refresh_token:
            response = requests.post(
                f"{ZIMFARM_API_URL}/auth/refresh",
                json={
                    "refresh_token": self._refresh_token,
                },
                timeout=HTTP_REQUEST_TIMEOUT,
            )
        else:
            response = requests.post(
                f"{ZIMFARM_API_URL}/auth/authorize",
                json={
                    "username": ZIMFARM_USERNAME,
                    "password": ZIMFARM_PASSWORD,
                },
                timeout=HTTP_REQUEST_TIMEOUT,
            )

        response.raise_for_status()
        payload = response.json()
        self._access_token = cast(str, payload["access_token"])
        self._refresh_token = cast(str, payload["refresh_token"])
        self._expires_at = datetime.datetime.fromisoformat(
            payload["expires_time"]
        ).replace(tzinfo=None)

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Retrieve or generate access token depending on if token has expired."""
        now = getnow()
        if (
            force_refresh
            or self._access_token is None
            or now >= (self._expires_at - ZIMFARM_TOKEN_RENEWAL_WINDOW)
        ):
            if AUTH_MODE == "oauth":
                self._generate_oauth_access_token()
            elif AUTH_MODE == "local":
                self._generate_local_access_token()
            else:
                raise ValueError(
                    f"Unknown cms authentication mode: {AUTH_MODE}. "
                    "Allowed values are: 'local', 'oauth'"
                )
        if self._access_token is None:
            raise ValueError("Failed to generate access token.")
        return self._access_token


def get_last_modified_for(url: str) -> str | None:
    """the Last-Modified header for an URL"""
    with requests.head(url, allow_redirects=True, timeout=HTTP_REQUEST_TIMEOUT) as resp:
        if resp.status_code == 404:
            raise FileNotFoundError(url)
        return resp.headers.get("last-modified")


def query_api(
    token: str,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    attempt: int = 0,
) -> tuple[bool, int, dict[str, Any]]:
    """success, status_code, payload from a query to Zimfarm API"""
    func = {
        "GET": requests.get,
        "POST": requests.post,
        "PATCH": requests.patch,
        "DELETE": requests.delete,
        "PUT": requests.put,
    }.get(method.upper(), requests.get)

    req_headers = {}
    req_headers.update(headers or {})
    try:
        req_headers.update({"Authorization": f"Bearer {token}"})
        req = func(
            url=url,
            headers=req_headers,
            json=payload,
            params=params,
            allow_redirects=False,
        )
    except Exception as exc:
        attempt += 1
        logger.exception(
            f"ConnectionError (attempt {attempt}) for {method} {url} -- {exc}"
        )
        if attempt <= 3:
            time.sleep(attempt * 60 * 2)
            return query_api(token, method, url, payload, params, headers, attempt)
        return (False, 599, {})

    if req.status_code == requests.codes.NO_CONTENT:
        return True, req.status_code, {}

    try:
        resp = req.json() if req.text else {}
    except json.JSONDecodeError:
        logger.exception(f"ResponseError (not JSON): -- {req.text}")
        return (False, req.status_code, {})
    except Exception as exc:
        logger.exception(f"ResponseError -- {exc} -- {req.text}")
        return (
            False,
            req.status_code,
            {},
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

    logger.error(content)

    return (False, req.status_code, {})


class WatcherRunner:
    def __init__(
        self,
        *,
        s3_url_with_credentials: str,
        s3_summary_file_url: str | None,
        schedule_on_update: bool,
        nb_threads: int,
        duration: str,
        work_dir: str,
        only: list[str] | None,
        runonce: bool,
        debug: bool = False,
    ):
        self.running = True
        self.s3_url_with_credentials = s3_url_with_credentials
        self.s3_summary_file_url = s3_summary_file_url
        self.schedule_on_update = schedule_on_update
        self.nb_threads = nb_threads
        self.duration = duration
        self.work_dir = work_dir
        self.only = only
        self.runonce = runonce
        self.debug = debug
        self._token_provider = ClientTokenProvider()

        # registering exit signals
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGQUIT, self.exit_gracefully)

    @property
    def work_dir(self):
        return self._work_dir

    @work_dir.setter
    def work_dir(self, value: str):
        self._work_dir = pathlib.Path(value).expanduser()
        self._work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def duration(self):
        return datetime.timedelta(seconds=self._duration)

    @duration.setter
    def duration(self, value: str):
        self._duration = humanfriendly.parse_timespan(value)

    def s3_credentials_ok(self) -> bool:
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

    def query_api(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> tuple[bool, int, dict[str, Any]]:
        """success, status_code, response for a query to Zimfarm API"""
        success, status_code, response = False, 0, {}

        try:
            access_token = self._token_provider.get_access_token()
        except Exception:
            logger.exception("Failed to get access token")
            return success, status_code, response

        attempts = 0
        while attempts <= 1:
            success, status_code, response = query_api(
                access_token,
                method,
                f"{ZIMFARM_API_URL}{path}",
                payload,
                params,
                headers or {},
            )
            attempts += 1

            # Unauthorised error: attempt to re-auth as scheduler might have restarted?
            if status_code == requests.codes.UNAUTHORIZED:
                try:
                    access_token = self._token_provider.get_access_token(
                        force_refresh=True
                    )
                except Exception:
                    logger.exception("Failed to get access token")
                continue
            else:
                break
        return success, status_code, response

    def zimfarm_credentials_ok(self) -> bool:
        logger.info(f"Testing Zimfarm credentials with {ZIMFARM_API_URL}…")
        success, _, _ = self.query_api("GET", "/auth/test")
        return success

    def retrieve_most_recent_dump_identifier(self) -> str:
        """retrieve the identifier of most recent Archive.org dump available"""
        resp = requests.get(QUERY_URL, timeout=HTTP_REQUEST_TIMEOUT)
        resp.raise_for_status()
        doc = resp.json()
        hits = doc.get("response", {}).get("body", {}).get("hits", None)
        if not hits:
            logger.error(
                "Impossible to parse query result, missing hits in response body:\n"
                f"{doc}\nStopping"
            )
            raise SystemExit(1)
        returned = hits.get("returned", None)
        if returned is None:
            logger.error(
                "Impossible to parse query result, missing returned in hits:\n"
                f"{doc}\nStopping"
            )
            raise SystemExit(1)
        if returned != 1:
            logger.error(
                f"Impossible to parse query result, returned is {returned}\nStopping"
            )
            raise SystemExit(1)
        hits = hits.get("hits", [])
        if len(hits) != 1:
            logger.error(
                "Impossible to parse query result, unexpected number of hits "
                f"{len(hits)}\nStopping"
            )
            raise SystemExit(1)
        hit = hits[0]
        identifier = hit.get("fields", {}).get("identifier", None)
        if identifier is None:
            logger.error(
                "Impossible to parse query result, missing identifier in first hit "
                f"{hit}\nStopping"
            )
            raise SystemExit(1)
        return identifier

    def retrieve_archives(self, identifier: str) -> list[str]:
        resp = requests.get(
            f"https://archive.org/download/{identifier}/{identifier}_files.xml",
            timeout=HTTP_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        parser = XMLtoDict()
        files = (
            parser.parse(resp.text)
            .get("files", {})
            .get("file", [])  # pyright: ignore[reportOptionalMemberAccess]
        )

        return [
            file["@name"]
            for file in files
            if file.get("format") == "7z"
            and file.get("@source") == "original"
            and "meta." not in file["@name"]
        ]

    def get_recipes_for(self, domain: str) -> list[str]:
        """list of Zimfarm recipes names for a StackExchange domain"""
        success, status, payload = self.query_api(
            "GET",
            "/recipes",
            params={"category": ["stack_exchange"], "name": f"{domain}_"},
        )
        if not success:
            logger.error(f"Can't get `{domain}` recipes from zimfarm")
            return []

        # filter by recipe name exactly starting with domain name, since API call
        # search for the domain "anywhere" in the recipe name
        return [
            recipe["name"]
            for recipe in payload.get("items", [])
            if recipe["enabled"] and recipe["name"].startswith(f"{domain}_")
        ]

    def blocked_by_zimfarm(self, domain: str) -> bool:
        """Whether a Zimfarm task is using its file now, preventing removal"""
        prefix = f" [{domain}]"
        logger.info(f"{prefix} Getting recipes depending on it")

        recipes = self.get_recipes_for(domain)
        if not recipes:
            logger.info(f"No recipes found for {domain}")
            return False

        success, status, payload = self.query_api(
            "GET",
            "/tasks",
            params={"recipe_name": recipes, "status": ["started", "scraper_started"]},
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
                logger.debug(f"{prefix} Zimfarm task #{task['id']} is blocking it")
                return True

        return False

    def unscheduled_in_zimfarm(self, domain: str):
        """Whether there was a pending task on Zimfarm that would have used this file

        Should there as been, this would unrequest it.
        """
        prefix = f" [{domain}]"
        recipes = self.get_recipes_for(domain)
        if not recipes:
            return False

        success, status, payload = self.query_api(
            "GET", "/requested-tasks", params={"recipe_name": recipes}
        )
        if not success:
            logger.error(f"{prefix} Can't get requested-tasks from zimfarm")
            return False

        tasks = payload.get("items", [])
        if not tasks:
            return False

        for task in tasks:
            self.query_api("DELETE", f"/requested-tasks/{task['id']}")
            logger.debug(f"{prefix} Zimfarm requested-task #{task['id']} deleted")

        return True

    def schedule_in_zimfarm(self, domain: str) -> list[str]:
        """Schedule matching recipes in Zimfarm as a new dump was uploaded"""
        recipes = self.get_recipes_for(domain)
        if not recipes:
            logger.info(f"No matching recipes for {domain} on zimfarm")
            return []

        success, status, payload = self.query_api(
            "POST", "/requested-tasks", payload={"recipe_names": recipes}
        )
        if not success:
            logger.error(
                f"Failed to create tasks for {recipes} with HTTP {status}: {payload}"
            )
            return []

        return payload.get("requested", [])

    def update_file(self, url: str, key: str, last_modified: str | None):
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
            obsolete = self.s3_storage.get_object_stat(
                key
            ).meta.get(  # pyright: ignore[reportOptionalMemberAccess]
                "lastmodified"
            )
            self.s3_storage.delete_object(key)
            logger.info(f"{prefix} Removed object (was from {obsolete})")

        logger.info(f"{prefix} Downloading…")
        fpath = self.work_dir / key

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
        self.s3_storage.upload_file(
            fpath=fpath, key=key, meta={"lastmodified": last_modified}
        )
        logger.info(f"{prefix} Uploaded")

        fpath.unlink()
        logger.info(f"{prefix} Local file removed")

        if self.schedule_on_update:
            logger.info(f"{prefix} Scheduling recipe on Zimfarm")
            scheduled = self.schedule_in_zimfarm(domain)
            if scheduled:
                logger.info(f"{prefix} scheduled: {', '.join(scheduled)}")
            elif scheduled is False:
                logger.info(f"{prefix} no recipe to schedule")
            else:
                logger.warning(f"{prefix} couldn't schedule recipe(s)")

    def retrieve_cached_summary(self) -> dict[str, Any] | None:
        if not self.s3_summary_file_url:
            return None
        resp = requests.get(self.s3_summary_file_url, timeout=HTTP_REQUEST_TIMEOUT)
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        resp.raise_for_status()
        summary = json.loads(resp.text)
        logger.info("Retrieved summary file...")
        return summary

    def check_and_go(self):
        logger.info("Getting most recent dump")
        identifier = self.retrieve_most_recent_dump_identifier()
        logger.info(f"Most recent dump is {identifier}")

        archives = self.retrieve_archives(identifier)
        logger.info(f"{len(archives)} archives found in {identifier} dump")
        logger.info("Grabbing online versions and comparing with S3…")

        cached_summary = self.retrieve_cached_summary()

        self.archives_futures = {}  # future: key
        self.archives_executor = cf.ThreadPoolExecutor(max_workers=self.nb_threads)

        for archive in archives:
            url = f"https://archive.org/download/{identifier}/{archive}"

            key = archive.split("/")[-1]
            last_modified = get_last_modified_for(url)

            if not self.s3_storage.has_object_matching(
                key, meta={"lastmodified": last_modified}
            ):
                logger.info(f" [+] {key} (from {last_modified})")

                future = self.archives_executor.submit(
                    self.update_file,
                    url=url,
                    key=key,
                    last_modified=last_modified,
                )
                self.archives_futures.update({future: key})

        if not self.archives_futures:
            logger.info("All synced up.")

        result = cf.wait(self.archives_futures.keys(), return_when=cf.FIRST_EXCEPTION)
        self.archives_executor.shutdown()

        for future in result.done:
            exc = future.exception()
            if exc:
                key = self.archives_futures.get(future)
                logger.error(f"Error processing {key}: {exc}")
                traceback.print_exception(exc)

        if result.not_done:
            logger.error(
                "Got some not_done files: \n - "
                + "\n - ".join(
                    [
                        self.archives_futures.get(future, "Unknown")
                        for future in result.not_done
                    ]
                )
            )

        new_summary = {
            "archives": [archive.split("/")[-1][:-3] for archive in archives]
        }
        if new_summary != cached_summary:
            logger.info("Updating summary in S3")
            cached_archives_fpath = pathlib.Path(SUMMARY_FILENAME)
            cached_archives_fpath.write_text(json.dumps(new_summary, indent=True))
            self.s3_storage.upload_file(
                fpath=cached_archives_fpath,
                key=SUMMARY_FILENAME,
                meta={"lastmodified": datetime.datetime.now().isoformat()},
            )
            cached_archives_fpath.unlink()

        logger.info("Done.")
        return not result.not_done

    def run(self):
        logger.info(ASCII_LOGO)

        if self.s3_url_with_credentials and not self.s3_credentials_ok():
            raise ValueError("Unable to connect to Optimization Cache. Check its URL.")

        if not self.s3_summary_file_url:
            self.s3_summary_file_url = (
                f"http://{self.s3_storage.bucket_name}.{self.s3_storage.url.netloc}/"
                f"{SUMMARY_FILENAME}"
            )

        if not self.zimfarm_credentials_ok():
            raise ValueError("Unable to connect to Zimfarm. Check credentials.")

        logger.info(
            f"Starting watcher:\n"
            f"  using cache: {self.s3_storage.url.netloc}\n"
            f"  with bucket: {self.s3_storage.bucket_name}"
            + (
                ("\n  only for:\n   - " + "\n   - ".join(self.only))
                if self.only
                else ""
            )
        )

        checked_on = datetime.datetime.now()
        self.check_and_go()
        while self.running and not self.runonce:
            if datetime.datetime.now() > checked_on + self.duration:
                checked_on = datetime.datetime.now()
                self.check_and_go()
            time.sleep(5)  # check time every 5s

    def exit_gracefully(self, signum, frame):
        signame = signal.strsignal(signum)
        self.running = False
        logger.info(f"received exit signal ({signame}).")
        sys.exit(1)


def rebuild_s3_url(uri: str):
    upload_uri = cast(urllib.parse.ParseResult, urllib.parse.urlparse(uri))

    def get_url_scheme(url: urllib.parse.ParseResult) -> str:
        if url.scheme.startswith("s3+http"):
            return "http"
        # covers both "s3" and "s3+https"
        elif url.scheme.startswith("s3") or url.scheme.startswith("s3+https"):
            return "https"
        else:
            raise ValueError(f"Unsupported URL scheme in: {url}")

    netloc = ""
    if upload_uri.username:
        netloc += upload_uri.username
    if upload_uri.password:
        netloc += f":{upload_uri.password}"

    if upload_uri.username or upload_uri.password:
        netloc += "@"

    if upload_uri.hostname:
        netloc += upload_uri.hostname

    if upload_uri.port:
        netloc += f":{upload_uri.port}"

    return urllib.parse.urlparse(
        urllib.parse.urlunparse(
            [
                get_url_scheme(upload_uri),
                netloc,
                upload_uri.path,
                upload_uri.fragment,
                upload_uri.query,
                upload_uri.fragment,
            ]
        )
    ).geturl()


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
        type=rebuild_s3_url,
    )

    parser.add_argument(
        "--s3-summary-file-url",
        help="S3 URL of caching dumps.",
        default=os.getenv("S3_SUMMARY_FILE_URL"),
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
        help="How many threads to run to parallelize download/upload? Defaults to 1",
        dest="nb_threads",
        type=int,
        default=1,
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
        "--runonce",
        help="Run only one check and stops",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--version",
        help="Display version and exit",
        action="version",
        version=VERSION,
    )

    args = parser.parse_args()

    if AUTH_MODE == "local":
        if not (ZIMFARM_USERNAME and ZIMFARM_PASSWORD):
            raise OSError(
                "ZIMFARM_USERNAME and ZIMFARM_PASSWORD must be set when AUTH_MODE is 'local'"
            )
    elif AUTH_MODE == "oauth":
        if not (
            ZIMFARM_OAUTH_CLIENT_ID,
            ZIMFARM_OAUTH_CLIENT_SECRET,
            ZIMFARM_OAUTH_AUDIENCE_ID,
        ):
            raise OSError(
                "ZIMFARM_OAUTH_CLIENT_ID, ZIMFARM_OAUTH_CLIENT_SECRET and "
                "ZIMFARM_OAUTH_AUDIENCE_ID must be set when AUTH_MODE is 'oauth'."
            )
    else:
        raise ValueError(
            f"Unsupported value '{AUTH_MODE}' for AUTH_MODE. Only 'local' and 'oauth' "
            "are supported."
        )
    runner = WatcherRunner(
        s3_url_with_credentials=args.s3_url_with_credentials,
        s3_summary_file_url=args.s3_summary_file_url,
        schedule_on_update=args.schedule_on_update,
        nb_threads=args.nb_threads,
        duration=args.duration,
        work_dir=args.work_dir,
        only=args.only,
        runonce=args.runonce,
        debug=args.debug,
    )

    try:
        sys.exit(runner.run())
    except Exception as exc:
        logger.error(f"FAILED. An error occurred: {exc}")
        if runner.debug:
            logger.exception(exc)
        raise SystemExit(1)


if __name__ == "__main__":
    entrypoint()
