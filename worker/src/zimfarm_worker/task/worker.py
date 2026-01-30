import json
import shutil
import signal
import sys
import tarfile
import time
import urllib.parse
from collections import defaultdict
from http import HTTPStatus
from pathlib import Path
from typing import Any, cast

import ujson
from docker.errors import NotFound
from docker.models.containers import Container

from zimfarm_worker.common import getnow, logger
from zimfarm_worker.common.constants import (
    CONTAINER_TASK_IDENT,
    ENVIRONMENT,
    MONITORING_KEY,
    PROGRESS_CAPABLE_OFFLINERS,
)
from zimfarm_worker.common.docker import (
    RUNNING_STATUSES,
    container_logs,
    get_container_logs,
    get_container_name,
    get_ip_address,
    query_host_mounts,
    query_host_stats,
    start_checker,
    start_dnscache,
    start_monitor,
    start_scraper,
    start_uploader,
)
from zimfarm_worker.common.utils import format_key, format_size
from zimfarm_worker.common.worker import BaseWorker
from zimfarm_worker.task.zim import get_zim_info

SLEEP_INTERVAL = 60  # nb of seconds to sleep before watching
CPU_EWMA_ALPHA = 0.01  # EWMA smoothing factor for CPU percentage samples (0..1)


PENDING = "pending"
DOING = "doing"
DONE = "done"
FAILED = "failed"
SKIPPED = "skipped"
MAX_ZIM_UPLOAD_RETRIES = 5
MAX_CHK_UPLOAD_RETRIES = 5
ZIM_UPLOAD = "zim_upload"
ZIM_CHECK = "check"
CHK_UPLOAD = "check_upload"
LOG_UPLOAD = "log_upload"
ARTIFACTS_UPLOAD = "artifacts_upload"


class TaskWorker(BaseWorker):
    def __init__(
        self,
        username: str,
        webapi_uris: list[str],
        workdir: Path,
        task_id: str,
    ) -> None:
        super().__init__(username, webapi_uris, workdir)

        self.task_id = task_id

        self.print_config(
            username=username,
            webapi_uris=webapi_uris,
            workdir=workdir,
            task_id=task_id,
        )

        # check workdir
        self.check_workdir()

        # check SSH private key
        self.check_private_key()

        # ensure we have valid credentials
        self.check_auth()

        # ensure we have access to docker API
        self.check_docker()

        host_stats = query_host_stats(self.docker, self.workdir)
        logger.info(
            "Host hardware resources:"
            f"\n\tCPU : {host_stats.cpu.total} (total) ;  {host_stats.cpu.available} "
            "(avail)"
            f"\n\tRAM : {format_size(host_stats.memory.total)} (total) ;"
            f"  {format_size(host_stats.memory.available)} (avail)"
            f"\n\tDisk: {format_size(host_stats.disk.total)} (configured) ;"
            f"  {format_size(host_stats.disk.available)} (avail) ; "
            f"{format_size(host_stats.disk.used)} (reserved) ;"
            f"  {format_size(host_stats.disk.remaining)} (remaining)"
        )

        self.task: dict[str, Any] | None = None
        self.should_stop = False
        self.task_workdir: Path | None = None
        self.progress_file: Path | None = None
        self.host_task_workdir: Path | None = None  # path on host for task_dir

        self.dnscache: Container | None = None  # dnscache container
        self.dns: list[str] | None = None  # list of DNS IPs or None
        self.monitor: Container | None = None  # monitor container

        self.zim_files_actions_status: dict[str, dict[str, str]] = (
            {}
        )  # ZIM files registry
        self.zim_upload_retries: defaultdict[str, int] = defaultdict(
            int
        )  # ZIM files with upload errors (registry)
        self.zimcheck_files: dict[str, str] = {}  # ZIM check files registry
        self.zimcheck_upload_retries: defaultdict[str, int] = defaultdict(
            int
        )  # mapping of zimcheck file to number of upload retries

        # Upload status tracking for logs and artifacts
        self.upload_status: dict[str, str] = {
            LOG_UPLOAD: PENDING,
            ARTIFACTS_UPLOAD: PENDING,
        }

        self.zim_uploader: Container | None = None  # zim-files uploader container
        self.checker: Container | None = None  # zim-files checker container
        self.zimcheck_uploader: Container | None = (
            None  # zimcheck results uploader container
        )

        self.scraper: Container | None = None  # scraper container
        self.log_uploader: Container | None = None  # scraper log uploader container
        self.artifacts_uploader: Container | None = (
            None  # scraper artifacts uploader container
        )
        self.host_logsdir: Path | None = None  # path on host where logs are stored
        self.scraper_succeeded: bool | None = None  # whether scraper succeeded

        self.max_memory_usage: int = 0  # maximum memory used by scraper
        self.max_disk_usage: int = 0  # maximum disk used by scraper
        self.avg_cpu_usage: float = 0.0  # cpu exponential moving weighted average
        self.max_cpu_usage: float = 0.0  # maximum cpu percentage used by scraper
        self._nb_scraper_container_size_exceptions: int = (
            0  # nb of times exceptions regarding container size have been thrown
        )

        # register stop/^C
        self.register_signals()

    def get_task(self):
        logger.info(f"Fetching task details for {self.task_id}")
        response = self.query_api(method="GET", path=f"/tasks/{self.task_id}")
        if response.status_code == HTTPStatus.OK:
            self.task = (  # pyright: ignore[reportIncompatibleVariableOverride]
                response.json
            )
            return

        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.warning(f"task {self.task_id} doesn't exist")
        else:
            logger.warning(f"couldn't retrieve task detail for {self.task_id}")

    def patch_task(self, payload: dict[str, Any]):
        response = self.query_api(
            method="PATCH", path=f"/tasks/{self.task_id}", payload=payload
        )
        if response.status_code != HTTPStatus.NO_CONTENT:
            logger.warning(
                f"couldn't patch task status={payload['event']} "
                f"HTTP {response.status_code}: {response.json}"
            )

    def mark_task_started(self):
        logger.info("Updating task-status=started")
        self.patch_task({"event": "started", "payload": {}})

    def mark_scraper_started(self):
        logger.info("Updating task-status=scraper_started")
        if not self.scraper:
            logger.error("No scraper to update")
            return
        self.scraper.reload()
        self.patch_task(
            {
                "event": "scraper_started",
                "payload": {
                    "image": self.scraper.image.tags[  # pyright: ignore[reportOptionalMemberAccess]
                        -1
                    ],
                    "command": self.scraper.attrs["Config"]["Cmd"],
                    "log": Path(self.scraper.attrs["LogPath"]).name,
                },
            }
        )

    def mark_scraper_completed(self, exit_code: int, stdout: str, stderr: str):
        logger.info(f"Updating task-status=scraper_completed. Exit code: {exit_code}")
        self.patch_task(
            {
                "event": "scraper_completed",
                "payload": {"exit_code": exit_code, "stdout": stdout, "stderr": stderr},
            }
        )

    def _get_scraper_container_size(self) -> int:
        """Calculate the space taken by the scraper image plus R/W layer."""
        # We cannot  report writable layer size or image size because the Python Docker
        # SDK does not support it. Pending the approval of https://github.com/docker/docker-py/pull/3370
        # there's no other option than to use the raw API to get this information.
        # This should be removed once the upstream PR is accepted.
        if not self.scraper:
            return 0
        try:
            result = cast(
                dict[str, Any],
                self.docker.api._result(  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                    self.docker.api._get(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                        self.docker.api._url(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                            "/containers/{0}/json", self.scraper.name
                        ),
                        params={"size": True},
                    ),
                    True,
                ),
            )
            return result.get("SizeRootFs", 0) + result.get("SizeRw", 0)
        except Exception as exc:
            self._nb_scraper_container_size_exceptions += 1
            if self._nb_scraper_container_size_exceptions > 1:
                logger.warning(
                    f"Failed to get container disk usage: {exc!s}, "
                    f"nb_occurrence: {self._nb_scraper_container_size_exceptions}"
                )
            else:
                logger.exception("Failed to get container disk usage")
            return 0

    def _get_scraper_workdir_disk_usage(self) -> int:
        """
        Get disk usage of scraper container's task workdir in bytes.

        Calculates the actual disk space used by files in the scraper's
        task workdir (where ZIM files and other outputs are written).
        """
        if not self.task_workdir:
            return 0

        try:
            if self.task_workdir.exists() and self.task_workdir.is_dir():
                return sum(
                    f.stat().st_size
                    for f in self.task_workdir.rglob("*")
                    if f.is_file()
                )
            return 0
        except Exception:
            logger.exception("Failed to get scraper disk usage")
            return 0

    def _compute_scraper_cpu_stats(self, scraper_stats: dict[str, Any]) -> float:
        """
        Compute CPU usage statistics from scraper container stats.

        Calculates CPU percentage with EWMA smoothing to reduce effect of
        short spikes.
        """
        cpu_sample = 0.0
        cpu_stats = scraper_stats.get("cpu_stats", {})
        precpu_stats = scraper_stats.get("precpu_stats", {})
        prev_total = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        curr_total = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        prev_system = precpu_stats.get("system_cpu_usage", 0)
        curr_system = cpu_stats.get("system_cpu_usage", 0)

        delta_cpu = curr_total - prev_total
        delta_system = curr_system - prev_system
        online_cpus = cpu_stats.get("online_cpus", 0)

        if delta_system > 0 and delta_cpu >= 0 and online_cpus > 0:
            cpu_sample = (delta_cpu / float(delta_system)) * float(online_cpus) * 100.0

        # apply EWMA smoothing to reduce effect of short spikes
        if self.avg_cpu_usage == 0.0:
            self.avg_cpu_usage = cpu_sample
        else:
            self.avg_cpu_usage = (
                CPU_EWMA_ALPHA * cpu_sample
                + (1.0 - CPU_EWMA_ALPHA) * self.avg_cpu_usage
            )
        return cpu_sample

    def submit_scraper_progress(self):
        """report scraper statistics and logs to the API"""
        if not self.scraper:
            logger.error("No scraper to update")
            return
        self.scraper.reload()
        stdout = self.scraper.logs(stdout=True, stderr=False, tail=5000).decode("utf-8")
        stderr = self.scraper.logs(stdout=False, stderr=True, tail=5000).decode("utf-8")
        scraper_stats = self.scraper.stats(  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            stream=False
        )
        scraper_stats = cast(dict[str, Any], scraper_stats)

        # update statistics
        self.max_memory_usage = max(
            [
                scraper_stats.get("memory_stats", {}).get("usage", 0),
                self.max_memory_usage,
            ]
        )

        cpu_sample = self._compute_scraper_cpu_stats(scraper_stats)
        self.max_cpu_usage = max([cpu_sample, self.max_cpu_usage])

        disk_usage = (
            self._get_scraper_workdir_disk_usage() + self._get_scraper_container_size()
        )
        self.max_disk_usage = max([disk_usage, self.max_disk_usage])

        stats: dict[str, Any] = {
            "memory": {
                "max_usage": self.max_memory_usage,
            },
            "cpu": {
                "max_usage": self.max_cpu_usage,
                "avg_usage": round(self.avg_cpu_usage, 2),
            },
            "disk": {
                "max_usage": self.max_disk_usage,
            },
        }

        # fetch and compute progression from progress file
        progress: dict[str, Any] = {}
        if self.progress_file and self.progress_file.exists():
            try:
                with open(self.progress_file) as fh:
                    data = json.load(fh)
                    done = int(data.get("done", 0))
                    total = int(data.get("total", 100))
                    progress = {
                        "done": done,
                        "total": total,
                        "overall": int(done / total * 100),
                    }
                    # partialZim is optional
                    if data.get("partialZim") and isinstance(data["partialZim"], bool):
                        progress["partialZim"] = data["partialZim"]
            except Exception as exc:
                logger.warning(f"failed to load progress details: {exc}")
            else:
                logger.info(f"reporting {progress['overall']}%")

        if progress:
            logger.debug(f"Submitting scraper progress: {progress['overall']}%")

        payload: dict[str, Any] = {"stdout": stdout, "stderr": stderr, "stats": stats}
        if progress:
            payload["progress"] = progress

        self.patch_task(
            {
                "event": "scraper_running",
                "payload": payload,
            }
        )

    def mark_task_completed(self, status: str, **kwargs: Any):
        logger.info(f"Updating task-status={status}")
        event_payload: dict[str, Any] = {}
        event_payload.update(kwargs)

        event_payload["log"] = get_container_logs(
            self.docker,
            container_name=get_container_name(CONTAINER_TASK_IDENT, self.task_id),
            tail=2000,
        )

        self.patch_task({"event": status, "payload": event_payload})

    def mark_file_created(self, filename: str, filesize: int):
        human_fsize = format_size(filesize)
        logger.info(f"ZIM file created: {filename}, {human_fsize}")
        self.patch_task(
            {
                "event": "created_file",
                "payload": {"file": {"name": filename, "size": filesize}},
            }
        )

    def mark_file_completed(self, filename: str, status: str):
        logger.info(f"Updating file-status={status} for {filename}")
        self.patch_task({"event": f"{status}_file", "payload": {"filename": filename}})

    def mark_file_checked(
        self,
        filename: str,
        info: dict[str, Any],
        zimcheck_retcode: int,
    ):
        logger.info(f"Updating file check-result={zimcheck_retcode} for {filename}")
        self.patch_task(
            {
                "event": "checked_file",
                "payload": {
                    "filename": filename,
                    "result": zimcheck_retcode,
                    "info": info,
                },
            }
        )

    def mark_check_result_uploaded(
        self,
        filename: str,
        zimcheck_filename: str | None,
    ):
        logger.info(
            f"Updating file check-result-uploaded={zimcheck_filename} for {filename}"
        )
        self.patch_task(
            {
                "event": "check_results_uploaded",
                "payload": {
                    "filename": filename,
                    "check_filename": zimcheck_filename,
                },
            }
        )

    def setup_workdir(self):
        logger.info("Setting-up workdir")
        folder_name = f"{self.task_id}"
        host_mounts = query_host_mounts(self.docker, [self.workdir])

        self.task_workdir = self.workdir.joinpath(folder_name)
        self.task_workdir.mkdir(exist_ok=True)
        self.host_task_workdir = host_mounts[self.workdir].joinpath(folder_name)

        if (
            self.task
            and self.task["config"]["offliner"]["offliner_id"]
            in PROGRESS_CAPABLE_OFFLINERS
        ):
            self.progress_file = self.task_workdir.joinpath("task_progress.json")

    def cleanup_workdir(self):
        logger.info(f"Removing task workdir {self.workdir}")
        if not self.task_workdir:
            logger.error("No task workdir to remove")
            return
        zim_files: list[tuple[str, str]] = [
            (f.name, format_size(f.stat().st_size))
            for f in self.task_workdir.glob("*.zim")
        ]
        if zim_files:
            logger.warning(f"ZIM files exists. removing anyway: {zim_files}")
        try:
            shutil.rmtree(self.task_workdir)
        except Exception as exc:
            logger.error(f"Failed to remove workdir: {exc}")

    def start_dnscache(self):
        if not self.task:
            logger.error("No task to start DNS cache")
            return
        logger.info("Starting DNS cache")
        self.dnscache = start_dnscache(self.docker, self.task)
        self.dns = [
            get_ip_address(
                self.docker,
                self.dnscache.name,  # pyright: ignore[reportArgumentType]
            )
        ]
        logger.debug(f"DNS Cache started using IPs: {self.dns}")

    def start_monitor(self):
        if not self.task:
            logger.error("No task to start monitor")
            return
        logger.info("Starting resource monitor")
        self.monitor = start_monitor(
            self.docker,
            task=self.task,
            monitoring_key=MONITORING_KEY or format_key(self.fingerprint),
        )

    def start_scraper(self):
        if not self.task or not self.host_task_workdir:
            logger.error("No task to start scraper")
            return
        logger.info(f"Starting scraper. Expects files at: {self.host_task_workdir} ")
        self.scraper = start_scraper(
            self.docker,
            task=self.task,
            dns=self.dns,
            host_workdir=self.host_task_workdir,
        )

    def stop_container(self, which: str, timeout: int | None = None):
        logger.info(f"Stopping and removing {which}")
        container = getattr(self, which)
        if container:
            try:
                container.reload()
                container.stop(timeout=timeout)
                container.remove()
            except NotFound:
                logger.debug(".. already gone")
                return
            finally:
                container = None

    def update(self):
        # update scraper
        if not self.scraper:
            logger.error("No scraper to update")
            return
        self.scraper.reload()
        if self.dnscache:
            self.dnscache.reload()
        if self.monitor:
            self.monitor.reload()
        if self.zim_uploader:
            self.zim_uploader.reload()
        self.refresh_files_list()

    def stop(self):
        """stopping everything before exit (on term or end of task)"""
        logger.info("Stopping all containers and actions")
        self.should_stop = True
        for step in (
            "monitor",
            "dnscache",
            "scraper",
            "log_uploader",
            "artifacts_uploader",
            "zimcheck_uploader",
            "zim_uploader",
            "checker",
        ):
            try:
                self.stop_container(step)
            except Exception as exc:
                logger.warning(f"Failed to stop {step}: {exc}")
                logger.exception(exc)

    def wait_for_upload_containers(self, containers: list[str]):
        """Wait for upload containers to complete."""

        if not containers:
            return

        logger.debug(f"Waiting for uploads to complete: {', '.join(containers)}")

        check_methods = {
            "log_uploader": self.check_scraper_log_upload,
            "artifacts_uploader": self.check_scraper_artifacts_upload,
        }

        while True:
            # Check upload status and send updates to API
            for container in containers:
                if container in check_methods:
                    check_methods[container]()

            still_running: list[str] = []
            for container in containers:
                if self.container_running(container):
                    still_running.append(container)

            if not still_running:
                logger.info("All upload containers completed")
                break

            logger.debug(f"Still waiting for: {', '.join(still_running)}")
            time.sleep(5)

    def exit_gracefully(self, signum: int, _: Any):
        signame = signal.strsignal(signum)
        logger.info(f"received exit signal ({signame}), shutting down…")

        # Try to upload logs and artifacts before stopping everything
        logger.info("Attempting to upload logs and artifacts before cancellation...")
        try:
            if self.scraper:
                try:
                    self.scraper.reload()

                    containers_to_wait: list[str] = []

                    if self.upload_status[LOG_UPLOAD] == PENDING:
                        self.upload_scraper_log()

                    if self.upload_status[LOG_UPLOAD] == DOING:
                        containers_to_wait.append("log_uploader")

                    if self.upload_status[ARTIFACTS_UPLOAD] == PENDING:
                        self.upload_scraper_artifacts()

                    if self.upload_status[ARTIFACTS_UPLOAD] == DOING:
                        containers_to_wait.append("artifacts_uploader")

                    if containers_to_wait:
                        logger.info(
                            "Notifying API of cancellation with "
                            "pending uploads of logs/artifacts"
                        )
                        self.patch_task(
                            {
                                "event": "canceling",
                                "payload": {},
                            }
                        )

                    self.wait_for_upload_containers(containers_to_wait)
                except NotFound:
                    logger.warning(
                        "Scraper container not found, skipping log/artifact upload"
                    )
                except Exception as exc:
                    logger.warning(
                        f"Error during log/artifact upload on cancellation: {exc}"
                    )
                    logger.exception(exc)
            else:
                logger.warning("No scraper container, skipping log/artifact upload")
        except Exception as exc:
            logger.error(f"Unexpected error during cancellation upload attempt: {exc}")
            logger.exception(exc)

        self.stop()
        self.cleanup_workdir()
        self.mark_task_completed("canceled", canceled_by=f"task shutdown ({signame})")
        sys.exit(1)

    def shutdown(self, status: str, **kwargs: Any):
        self.mark_task_completed(status, **kwargs)
        logger.info("Shutting down task-worker")
        self.stop()
        self.cleanup_workdir()

    def start_zim_uploader(self, upload_dir: Path, filename: str):
        logger.info(f"Starting zim uploader for {upload_dir}/{filename}")
        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start zim uploader")
            return
        self.zim_uploader = start_uploader(
            self.docker,
            task=self.task,
            kind="zim",
            username=self.username,
            host_workdir=self.host_task_workdir,
            upload_dir=upload_dir,
            filename=filename,
            move=True,
            delete=False,  # zim delete on task exit to allow parallel zimcheck
            compress=False,
            resume=False,
        )

    def start_checker(self, filename: str):
        logger.info(f"Starting zim checker for {filename}")
        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start zim checker")
            return
        self.checker = start_checker(
            self.docker,
            task=self.task,
            host_workdir=self.host_task_workdir,
            filename=filename,
        )

    def start_zimcheck_uploader(self, filename: str):
        logger.info(f"Starting zimcheck uploader for {filename}")

        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start zimcheck uploader")
            return

        self.zimcheck_uploader = start_uploader(
            self.docker,
            task=self.task,
            kind="check",
            username=self.username,
            host_workdir=self.host_task_workdir,
            upload_dir="",
            filename=filename,
            move=False,
            delete=False,
            compress=False,
            resume=False,
        )

    def upload_zimcheck_results(self):
        """Upload results of zim checker saved to disk"""

        # check if zimcheck uploader is running
        if self.zimcheck_uploader:
            self.zimcheck_uploader.reload()

        if self.zimcheck_uploader and self.zimcheck_uploader.status in RUNNING_STATUSES:
            # still running, nothing to do
            return

        # not running but was running
        if self.zimcheck_uploader:
            zimcheck_filename = cast(
                str,
                self.zimcheck_uploader.labels[  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                    "filename"
                ],
            )
            # get results of container
            exit_code = self.zimcheck_uploader.attrs["State"]["ExitCode"]
            logger.info(
                f"Zimcheck Uploader for {zimcheck_filename} complete {exit_code}"
            )
            if exit_code == 0:
                zim_file = self.zimcheck_files[zimcheck_filename]
                self.zim_files_actions_status[zim_file][CHK_UPLOAD] = DONE
                self.mark_check_result_uploaded(
                    filename=zim_file,
                    zimcheck_filename=zimcheck_filename,
                )
                del self.zimcheck_files[zimcheck_filename]
                # Delete these files as they might be big
                if self.task_workdir:
                    (self.task_workdir / zimcheck_filename).unlink(missing_ok=True)
            else:
                logger.error(
                    "Zimcheck Uploader:: "
                    f"{get_container_logs(self.docker, self.zimcheck_uploader.name)}"  # pyright: ignore[reportArgumentType]
                )
                self.zimcheck_upload_retries[zimcheck_filename] += 1
                if (
                    self.zimcheck_upload_retries[zimcheck_filename]
                    >= MAX_CHK_UPLOAD_RETRIES
                ):
                    logger.error(
                        f"{zimcheck_filename} exhausted retries "
                        f"{MAX_CHK_UPLOAD_RETRIES}"
                    )
                    zim_file = self.zimcheck_files[zimcheck_filename]
                    self.zim_files_actions_status[zim_file][CHK_UPLOAD] = FAILED
                    del self.zimcheck_files[zimcheck_filename]
                    if self.task_workdir:
                        (self.task_workdir / zimcheck_filename).unlink(missing_ok=True)
                else:
                    zim_file = self.zimcheck_files[zimcheck_filename]
                    self.zim_files_actions_status[zim_file][CHK_UPLOAD] = PENDING

            self.zimcheck_uploader.remove()
            self.zimcheck_uploader = None

        # Start a zimcheck results uploader instance
        if (
            self.zimcheck_uploader is None
            and len(self.zimcheck_files) > 0
            and not self.should_stop
        ):
            try:
                zimcheck_file = set(self.zimcheck_files.keys()).pop()
            except KeyError:
                logger.debug("No zimcheck files to upload")
            else:
                zim_file = self.zimcheck_files[zimcheck_file]
                self.zim_files_actions_status[zim_file][CHK_UPLOAD] = DOING
                self.start_zimcheck_uploader(zimcheck_file)

    def container_running(self, which: str) -> bool:
        """whether refered container is still running or not"""
        container = getattr(self, which)
        if not container:
            return False
        try:
            container.reload()
        except NotFound:
            return False
        return container.status in RUNNING_STATUSES

    def upload_scraper_log(self):
        # Skip if already done or in progress
        if self.upload_status[LOG_UPLOAD] in (DONE, DOING, FAILED):
            logger.debug(f"Log upload already {self.upload_status[LOG_UPLOAD]}")
            return

        if not self.scraper:
            logger.error("No scraper to upload it's logs…")
            self.upload_status[LOG_UPLOAD] = SKIPPED
            return  # scraper gone, we can't access log

        if not self.task:
            logger.error("No task to upload scraper log")
            self.upload_status[LOG_UPLOAD] = SKIPPED
            return

        logger.debug("Dumping docker logs to file…")
        filename = (
            f"{self.task['id']}_{self.task['config']['offliner']['offliner_id']}.log"
        )
        if not self.task_workdir:
            logger.error("No task workdir to upload scraper log")
            return

        fpath = self.task_workdir / filename
        try:
            with open(fpath, "wb") as fh:
                for line in container_logs(
                    self.docker,
                    container=self.scraper.name,
                    stdout=True,
                    stderr=True,
                    stream=True,
                ):
                    fh.write(line)
        except Exception as exc:
            logger.error(f"Unable to dump logs to {fpath}")
            logger.exception(exc)
            self.upload_status[LOG_UPLOAD] = FAILED
            return

        logger.debug("Starting log uploader container…")
        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start log uploader")
            self.upload_status[LOG_UPLOAD] = SKIPPED
            return

        self.upload_status[LOG_UPLOAD] = DOING
        self.log_uploader = start_uploader(
            self.docker,
            task=self.task,
            kind="logs",
            username=self.username,
            host_workdir=self.host_task_workdir,
            upload_dir="",
            filename=filename,
            move=False,
            delete=True,
            compress=True,
            resume=True,
        )

    def check_scraper_log_upload(self) -> bool:
        """Check if log upload is complete and update status."""
        # Already processed
        if self.upload_status[LOG_UPLOAD] in (DONE, FAILED, SKIPPED):
            return True

        if not self.log_uploader:
            return False

        if self.container_running("log_uploader"):
            return False

        try:
            self.log_uploader.reload()
            exit_code = self.log_uploader.attrs["State"]["ExitCode"]
            filename = self.log_uploader.labels[  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                "filename"
            ]
        except NotFound:
            # prevent race condition if re-entering between this and container removal
            return False

        logger.info(f"Scraper log upload complete: {exit_code}")

        if exit_code == 0:
            self.upload_status[LOG_UPLOAD] = DONE
            logger.info(f"Sending scraper log filename: {filename}")
            self.patch_task(
                {
                    "event": "update",
                    "payload": {"log": filename},
                }
            )
        else:
            self.upload_status[LOG_UPLOAD] = FAILED
            logger.error(
                f"Log Uploader:: "
                f"{get_container_logs(self.docker, self.log_uploader.name)}"  # pyright: ignore[reportArgumentType]
            )

        self.stop_container("log_uploader")
        return True

    def upload_scraper_artifacts(self):
        # Skip if already done or in progress
        if self.upload_status[ARTIFACTS_UPLOAD] in (DONE, DOING, FAILED):
            logger.debug(
                f"Artifacts upload already {self.upload_status[ARTIFACTS_UPLOAD]}"
            )
            return

        if not self.scraper:
            logger.error("No scraper to upload its artifacts…")
            self.upload_status[ARTIFACTS_UPLOAD] = SKIPPED
            return  # scraper gone, we can't access artifacts

        if not self.task:
            logger.error("No task to upload scraper artifacts")
            self.upload_status[ARTIFACTS_UPLOAD] = SKIPPED
            return

        if (
            "upload" not in self.task
            or "artifacts" not in self.task["upload"]
            or "upload_uri" not in self.task["upload"]["artifacts"]
            or not self.task["upload"]["artifacts"]["upload_uri"]
        ):
            logger.debug("No artifacts upload URI configured")
            self.upload_status[ARTIFACTS_UPLOAD] = SKIPPED
            return

        artifacts_globs = self.task["config"].get("artifacts_globs", None)
        if not artifacts_globs:
            logger.debug("No artifacts configured for upload")
            self.upload_status[ARTIFACTS_UPLOAD] = SKIPPED
            return
        else:
            logger.debug(f"Archiving files matching {artifacts_globs}")

        logger.debug("Creating a tar of requested artifacts")
        filename = (
            f"{self.task['id']}_{self.task['config']['offliner']['offliner_id']}.tar"
        )
        if not self.task_workdir:
            logger.error("No task workdir to upload scraper artifacts")
            self.upload_status[ARTIFACTS_UPLOAD] = SKIPPED
            return

        fpath = self.task_workdir / filename
        try:
            files_to_archive = [
                file
                for pattern in artifacts_globs
                for file in self.task_workdir.glob(pattern)
            ]
            if len(files_to_archive) == 0:
                logger.debug("No files found to archive")
                self.upload_status[ARTIFACTS_UPLOAD] = SKIPPED
                return

            with tarfile.open(fpath, "w") as tar:
                for file in files_to_archive:
                    tar.add(file, arcname=file.relative_to(self.task_workdir))
                    try:
                        file.unlink(missing_ok=True)
                    except Exception as exc:
                        logger.debug(
                            "Unable to delete file after archiving", exc_info=exc
                        )
        except Exception as exc:
            logger.error(f"Unable to archive artifacts to {fpath}")
            logger.exception(exc)
            self.upload_status[ARTIFACTS_UPLOAD] = FAILED
            return

        logger.debug("Starting artifacts uploader container…")
        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start artifacts uploader")
            self.upload_status[ARTIFACTS_UPLOAD] = SKIPPED
            return

        self.upload_status[ARTIFACTS_UPLOAD] = DOING
        self.artifacts_uploader = start_uploader(
            self.docker,
            task=self.task,
            kind="artifacts",
            username=self.username,
            host_workdir=self.host_task_workdir,
            upload_dir="",
            filename=filename,
            move=False,
            delete=True,
            compress=True,
            resume=True,
        )

    def check_scraper_artifacts_upload(self) -> bool:
        """Check if artifacts upload is complete and update status."""
        # Already processed
        if self.upload_status[ARTIFACTS_UPLOAD] in (DONE, FAILED, SKIPPED):
            return True

        # Not started yet
        if not self.artifacts_uploader:
            return False

        # Still running
        if self.container_running("artifacts_uploader"):
            return False

        try:
            self.artifacts_uploader.reload()
            exit_code = self.artifacts_uploader.attrs["State"]["ExitCode"]
            filename = self.artifacts_uploader.labels[  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "filename"
            ]
        except NotFound:
            # prevent race condition if re-entering between this and container removal
            return False

        logger.info(f"Scraper artifacts upload complete: {exit_code}")

        if exit_code == 0:
            self.upload_status[ARTIFACTS_UPLOAD] = DONE
            logger.info(f"Sending scraper artifacts filename: {filename}")
            self.patch_task(
                {
                    "event": "update",
                    "payload": {"artifacts": filename},
                }
            )
        else:
            self.upload_status[ARTIFACTS_UPLOAD] = FAILED
            logger.error(
                f"Artifacts Uploader:: "
                f"{
                    get_container_logs(
                        self.docker,
                        container_name=self.artifacts_uploader.name,  # pyright: ignore[reportArgumentType]
                    )
                }"
            )

        self.stop_container("artifacts_uploader")
        return True

    def refresh_files_list(self):
        if not self.task_workdir:
            logger.error("No task workdir to refresh files list")
            return
        if not self.task:
            logger.error("No task to refresh files list")
            return
        for fpath in self.task_workdir.glob("*.zim"):
            if fpath.name not in self.zim_files_actions_status.keys():
                # append file to our watchlist
                self.zim_files_actions_status.update(
                    {
                        fpath.name: {
                            ZIM_UPLOAD: PENDING,
                            ZIM_CHECK: (
                                PENDING
                                if self.task["upload"]["zim"]["zimcheck"]
                                else SKIPPED
                            ),
                            CHK_UPLOAD: (
                                PENDING
                                if self.task["upload"]["zim"]["zimcheck"]
                                else SKIPPED
                            ),
                        }
                    }
                )
                # inform API about new file
                self.mark_file_created(fpath.name, fpath.stat().st_size)

    def pending_zim_files(self, kind: str) -> list[tuple[str, dict[str, str]]]:
        """shortcut list of watched file in PENDING status for upload or check"""
        return list(
            filter(
                lambda x: x[1][kind] == PENDING, self.zim_files_actions_status.items()
            )
        )

    @property
    def busy_zim_files(self) -> list[tuple[str, dict[str, str]]]:
        """list of files preventing worker to exit

        including PENDING as those have not been uploaded/checked
        including DOING as those might fail and go back to PENDING"""
        return list(
            filter(
                lambda x: x[1][ZIM_UPLOAD] in (PENDING, DOING)
                or x[1][ZIM_CHECK] in (PENDING, DOING)
                or x[1][CHK_UPLOAD] in (PENDING, DOING),
                self.zim_files_actions_status.items(),
            )
        )

    @property
    def zim_file_uploads_complete(self) -> bool:
        """Check if all ZIM file uploads are complete"""
        if len(self.zim_files_actions_status) == 0:
            return False

        for _, actions in self.zim_files_actions_status.items():
            # ZIM upload must be DONE
            if actions[ZIM_UPLOAD] != DONE:
                return False

            # zimcheck must be DONE or SKIPPED
            if actions[ZIM_CHECK] not in (DONE, SKIPPED):
                return False

            # chk_upload must be DONE or SKIPPED
            if actions[CHK_UPLOAD] not in (DONE, SKIPPED):
                return False

        return True

    def check_zims(self):
        if not self.task:
            logger.error("No task to check files")
            return
        if not self.task["upload"]["zim"]["zimcheck"]:
            return
        if not self.task_workdir:
            logger.error("No task workdir to check files")
            return

        self.refresh_files_list()

        # check if checker running
        if self.checker:
            self.checker.reload()

        if self.checker and self.checker.status in RUNNING_STATUSES:
            # still running, nothing to do
            return

        # not running but _was_ running
        if self.checker:
            # find file
            zim_file = self.checker.labels[  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                "filename"
            ]
            self.zim_files_actions_status[zim_file][ZIM_CHECK] = DONE

            # get result of container
            zimcheck_log = get_container_logs(
                self.docker,
                self.checker.name,  # pyright: ignore[reportArgumentType]
            ).strip()

            logger.info(f"Gathering ZIM metadata for {zim_file}")
            zim_info = get_zim_info(
                self.task_workdir
                / zim_file  # pyright: ignore[reportUnknownArgumentType]
            )

            try:
                zimcheck_result = ujson.loads(zimcheck_log)
            except Exception as exc:
                # Failed to parse JSON, send raw log
                zimcheck_result = None
                logger.warning(f"Failed to parse zimcheck output: {exc}")
            else:
                zimcheck_log = None

            zimcheck_file_content: dict[str, Any] = {
                "filename": zim_file,
                "info": zim_info,
                "result": zimcheck_result,
                "log": zimcheck_log,
                "retcode": self.checker.attrs["State"]["ExitCode"],
            }
            self.mark_file_checked(
                filename=zim_file,  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
                zimcheck_retcode=zimcheck_file_content["retcode"],
                info=zim_info,
            )
            # zimcheck results could be too big, so, we write them to a file
            # https://github.com/openzim/zimfarm/issues/1456
            zimcheck_filename = f"{zim_info['id']}_zimcheck.json"
            try:
                with open(self.task_workdir / zimcheck_filename, "w") as f:
                    json.dump(zimcheck_file_content, f)
            except Exception:
                logger.exception(
                    f"Failed to write zimcheck output to {zimcheck_filename}"
                )
            else:
                logger.info(f"Zimcheck output written to {zimcheck_filename}")
                self.zimcheck_files[zimcheck_filename] = zim_file
                self.zim_files_actions_status[zim_file][CHK_UPLOAD] = PENDING
                del zimcheck_file_content

            self.checker.remove()
            self.checker = None

        # start a checker instance
        if (
            self.checker is None
            and self.pending_zim_files(ZIM_CHECK)
            and not self.should_stop
        ):
            try:
                zim_file, _ = self.pending_zim_files(ZIM_CHECK).pop()
            except Exception:
                # no more pending files,
                logger.debug("failed to get ZIM file: pending_zim_files empty")
            else:
                self.start_checker(zim_file)
                self.zim_files_actions_status[zim_file][ZIM_CHECK] = DOING

    def upload_zims(self):
        """manages self.zim_files

        - list files in folder to upload list
        - upload files one by one using dedicated uploader containers"""
        # check files in workdir and update our list of files to upload
        self.refresh_files_list()

        # check if uploader running
        if self.zim_uploader:
            self.zim_uploader.reload()

        if self.zim_uploader and self.zim_uploader.status in RUNNING_STATUSES:
            # still running, nothing to do
            return

        # not running but _was_ running
        if self.zim_uploader:
            # find file
            zim_file = cast(
                str,
                self.zim_uploader.labels[  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                    "filename"
                ],
            )
            # get result of container
            if self.zim_uploader.attrs["State"]["ExitCode"] == 0:
                self.zim_files_actions_status[zim_file][ZIM_UPLOAD] = DONE
                self.mark_file_completed(
                    zim_file,
                    "uploaded",
                )
            else:
                logger.error(
                    f"ZIM Uploader:: "
                    f"{get_container_logs(self.docker, self.zim_uploader.name)}"  # pyright: ignore[reportArgumentType]
                )
                self.zim_upload_retries[zim_file] = (
                    self.zim_upload_retries.get(
                        zim_file,
                        0,
                    )
                    + 1
                )
                if self.zim_upload_retries[zim_file] >= MAX_ZIM_UPLOAD_RETRIES:
                    logger.error(
                        f"{zim_file} exhausted retries ({MAX_ZIM_UPLOAD_RETRIES})"
                    )
                    self.zim_files_actions_status[zim_file][ZIM_UPLOAD] = FAILED
                    self.mark_file_completed(
                        zim_file,
                        "failed",
                    )
                else:
                    self.zim_files_actions_status[zim_file][ZIM_UPLOAD] = PENDING
            self.zim_uploader.remove()
            self.zim_uploader = None

        # start an uploader instance
        if not self.task:
            logger.error("No task to upload files")
            return
        if (
            self.zim_uploader is None
            and self.pending_zim_files(ZIM_UPLOAD)
            and not self.should_stop
        ):
            try:
                zim_file, _ = self.pending_zim_files(ZIM_UPLOAD).pop()
            except Exception:
                # no more pending files,
                logger.debug("failed to get ZIM file: pending_zim_files empty")
            else:
                self.start_zim_uploader(self.task["config"]["warehouse_path"], zim_file)
                self.zim_files_actions_status[zim_file][ZIM_UPLOAD] = DOING

    def handle_zims(self):
        self.upload_zims()
        self.check_zims()
        self.upload_zimcheck_results()

    def handle_stopped_scraper(self):
        if not self.scraper:
            logger.error("No scraper to handle stopped scraper")
            return
        self.scraper.reload()
        exit_code = self.scraper.attrs["State"]["ExitCode"]
        stdout = self.scraper.logs(stdout=True, stderr=False, tail=100).decode("utf-8")
        stderr = self.scraper.logs(stdout=False, stderr=True, tail=100).decode("utf-8")
        self.mark_scraper_completed(exit_code, stdout, stderr)
        self.scraper_succeeded = exit_code == 0
        self.upload_scraper_log()
        self.upload_scraper_artifacts()

    def sleep(self):
        time.sleep(1)

    def run(self):
        # get task detail from URL
        self.get_task()
        if self.task is None:
            logger.critical("Can't do much without task detail. exitting.")
            return 1
        self.mark_task_started()

        # prepare sub folder
        self.setup_workdir()

        if ENVIRONMENT != "development":
            # start our DNS cache
            self.start_dnscache()

        # start scraper
        self.start_scraper()
        self.mark_scraper_started()

        # monitor must be started after scraper to feed it the scraper IP
        if self.task["config"].get("monitor", False):
            self.start_monitor()

        self.submit_scraper_progress()

        last_check = getnow()

        while not self.should_stop and self.container_running("scraper"):
            now = getnow()
            if (now - last_check).total_seconds() < SLEEP_INTERVAL:
                self.sleep()
                continue

            last_check = now
            self.submit_scraper_progress()
            self.handle_zims()

        # scraper is done.
        # submit final progress (especially partialZim property)
        self.submit_scraper_progress()
        # check files so upload can continue
        self.handle_stopped_scraper()

        self.handle_zims()  # rescan folder

        # monitor upload/check of files
        while not self.should_stop and (
            self.busy_zim_files
            or self.container_running("zim_uploader")
            or self.container_running("checker")
            or self.container_running("log_uploader")
            or self.container_running("artifacts_uploader")
            or self.container_running("zimcheck_uploader")
        ):
            now = getnow()
            if (now - last_check).total_seconds() < SLEEP_INTERVAL:
                self.sleep()
                continue

            last_check = now
            self.handle_zims()
            self.check_scraper_log_upload()
            self.check_scraper_artifacts_upload()

        # make sure we submit upload status for last zim and scraper log
        self.log_workdir_entries()
        self.handle_zims()
        self.check_scraper_log_upload()
        self.check_scraper_artifacts_upload()

        # done with processing, cleaning-up and exiting
        self.shutdown(
            "succeeded"
            if (self.scraper_succeeded and self.zim_file_uploads_complete)
            else "failed"
        )

    def can_stream_logs(self):
        if not self.task:
            return False
        try:
            upload_uri = (  # pyright: ignore[reportUnknownVariableType]
                urllib.parse.urlparse(
                    self.task.get("upload", {}).get("logs", {}).get("upload_uri", 1)
                )
            )
        except Exception:
            return False
        return upload_uri.scheme in (  # pyright: ignore[reportUnknownMemberType]
            "scp",
            "sftp",
        )

    def log_workdir_entries(self):
        if not self.task_workdir:
            return
        logger.info(f"Contents of {self.task_workdir} (recursive):")
        for entry in self.task_workdir.rglob("*"):
            if entry.is_file():
                logger.info(f"  {entry.relative_to(self.task_workdir)}")
