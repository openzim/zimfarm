import json
import shutil
import signal
import sys
import tarfile
import time
from http import HTTPStatus
from pathlib import Path
from typing import Any

import ujson
from docker.errors import NotFound
from docker.models.containers import Container

from common import getnow, logger
from common.constants import (
    CONTAINER_TASK_IDENT,
    MONITORING_KEY,
    PROGRESS_CAPABLE_OFFLINERS,
)
from common.docker import (
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
from common.utils import format_key, format_size
from common.worker import BaseWorker
from task.zim import get_zim_info

SLEEP_INTERVAL = 60  # nb of seconds to sleep before watching
PENDING = "pending"
UPLOADING = "uploading"
UPLOADED = "uploaded"
FAILED = "failed"
CHECKING = "checking"
CHECKED = "checked"
SKIPPED = "skipped"
MAX_ZIM_RETRIES = 5
UP = "upload"
CHK = "check"


class TaskWorker(BaseWorker):
    task_id: str

    def __init__(self, **kwargs: Any) -> None:
        # print config
        self.print_config(**kwargs)

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

        self.zim_files: dict[str, dict[str, str]] = {}  # ZIM files registry
        self.zim_retries = {}  # ZIM files with upload errors (registry)
        self.uploader: Container | None = None  # zim-files uploader container
        self.checker: Container | None = None  # zim-files uploader container

        self.scraper: Container | None = None  # scraper container
        self.log_uploader: Container | None = None  # scraper log uploader container
        self.artifacts_uploader: Container | None = (
            None  # scraper artifacts uploader container
        )
        self.host_logsdir: Path | None = None  # path on host where logs are stored
        self.scraper_succeeded: bool | None = None  # whether scraper succeeded

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

    def submit_scraper_progress(self):
        """report last lines of scraper to the API"""
        if not self.scraper:
            logger.error("No scraper to update")
            return
        self.scraper.reload()
        stdout = self.scraper.logs(stdout=True, stderr=False, tail=5000).decode("utf-8")
        stderr = self.scraper.logs(stdout=False, stderr=True, tail=5000).decode("utf-8")
        scraper_stats = self.scraper.stats(  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            stream=False
        )
        stats: dict[str, Any] = {
            "memory": {
                "max_usage": scraper_stats.get(  # pyright: ignore[reportUnknownMemberType]
                    "memory_stats", {}
                ).get(
                    "max_usage"
                )
            }
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
        zimcheck_result: dict[str, Any] | None = None,
        zimcheck_log: str | None = None,
    ):
        logger.info(f"Updating file check-result={zimcheck_retcode} for {filename}")
        self.patch_task(
            {
                "event": "checked_file",
                "payload": {
                    "filename": filename,
                    "result": zimcheck_retcode,
                    "log": zimcheck_log,
                    "details": zimcheck_result,
                    "info": info,
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

        if self.task and self.task["config"]["task_name"] in PROGRESS_CAPABLE_OFFLINERS:
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
        if not self.task or not self.dns or not self.host_task_workdir:
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
        if self.uploader:
            self.uploader.reload()
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
            "uploader",
            "checker",
        ):
            try:
                self.stop_container(step)
            except Exception as exc:
                logger.warning(f"Failed to stop {step}: {exc}")
                logger.exception(exc)

    def exit_gracefully(self, signum: int, _: Any):
        signame = signal.strsignal(signum)
        logger.info(f"received exit signal ({signame}), shutting down…")
        self.stop()
        self.cleanup_workdir()
        self.mark_task_completed("canceled", canceled_by=f"task shutdown ({signame})")
        sys.exit(1)

    def shutdown(self, status: str, **kwargs: Any):
        self.mark_task_completed(status, **kwargs)
        logger.info("Shutting down task-worker")
        self.stop()
        self.cleanup_workdir()

    def start_uploader(self, upload_dir: Path, filename: str):
        logger.info(f"Gathering ZIM metadata for {upload_dir}/{filename}")

        logger.info(f"Starting uploader for {upload_dir}/{filename}")
        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start uploader")
            return
        self.uploader = start_uploader(
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
            logger.error("No task or host task workdir to start checker")
            return
        self.checker = start_checker(
            self.docker,
            task=self.task,
            host_workdir=self.host_task_workdir,
            filename=filename,
        )

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
        if not self.scraper:
            logger.error("No scraper to upload it's logs…")
            return  # scraper gone, we can't access log

        if not self.task:
            logger.error("No task to upload scraper log")
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
                    container_name=self.scraper.name,
                    stdout=True,
                    stderr=True,
                    stream=True,
                ):
                    fh.write(line)
        except Exception as exc:
            logger.error(f"Unable to dump logs to {fpath}")
            logger.exception(exc)
            return False

        logger.debug("Starting log uploader container…")
        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start log uploader")
            return
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

    def check_scraper_log_upload(self):
        if not self.log_uploader or self.container_running("log_uploader"):
            return

        try:
            self.log_uploader.reload()
            exit_code = self.log_uploader.attrs["State"]["ExitCode"]
            filename = self.log_uploader.labels[  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                "filename"
            ]
        except NotFound:
            # prevent race condition if re-entering between this and container removal
            return
        logger.info(f"Scraper log upload complete: {exit_code}")
        if exit_code != 0:
            logger.error(
                f"Log Uploader:: "
                f"{get_container_logs(self.docker, self.log_uploader.name)}"  # pyright: ignore[reportArgumentType]
            )
        self.stop_container("log_uploader")

        logger.info(f"Sending scraper log filename: {filename}")
        self.patch_task(
            {
                "event": "update",
                "payload": {"log": filename},
            }
        )

    def upload_scraper_artifacts(self):
        if not self.scraper:
            logger.error("No scraper to upload its artifacts…")
            return  # scraper gone, we can't access artifacts

        if not self.task:
            logger.error("No task to upload scraper artifacts")
            return

        if (
            "upload" not in self.task
            or "artifacts" not in self.task["upload"]
            or "upload_uri" not in self.task["upload"]["artifacts"]
            or not self.task["upload"]["artifacts"]["upload_uri"]
        ):
            logger.debug("No artifacts upload URI configured")
            return

        artifacts_globs = self.task["config"].get("artifacts_globs", None)
        if not artifacts_globs:
            logger.debug("No artifacts configured for upload")
            return
        else:
            logger.debug(f"Archiving files matching {artifacts_globs}")

        logger.debug("Creating a tar of requested artifacts")
        filename = (
            f"{self.task['id']}_{self.task['config']['offliner']['offliner_id']}.tar"
        )
        if not self.task_workdir:
            logger.error("No task workdir to upload scraper artifacts")
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
            return

        logger.debug("Starting artifacts uploader container…")
        if not self.task or not self.host_task_workdir:
            logger.error("No task or host task workdir to start artifacts uploader")
            return
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

    def check_scraper_artifacts_upload(self):
        if not self.artifacts_uploader or self.container_running("artifacts_uploader"):
            return

        try:
            self.artifacts_uploader.reload()
            exit_code = self.artifacts_uploader.attrs["State"]["ExitCode"]
            filename = self.artifacts_uploader.labels[  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                "filename"
            ]
        except NotFound:
            # prevent race condition if re-entering between this and container removal
            return
        logger.info(f"Scraper artifacts upload complete: {exit_code}")
        if exit_code != 0:
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

        logger.info(f"Sending scraper artifacts filename: {filename}")
        self.patch_task(
            {
                "event": "update",
                "payload": {"artifacts": filename},
            }
        )

    def refresh_files_list(self):
        if not self.task_workdir:
            logger.error("No task workdir to refresh files list")
            return
        if not self.task:
            logger.error("No task to refresh files list")
            return
        for fpath in self.task_workdir.glob("*.zim"):
            if fpath.name not in self.zim_files.keys():
                # append file to our watchlist
                self.zim_files.update(
                    {
                        fpath.name: {
                            UP: PENDING,
                            CHK: (
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
        return list(filter(lambda x: x[1][kind] == PENDING, self.zim_files.items()))

    @property
    def busy_zim_files(self) -> list[tuple[str, dict[str, str]]]:
        """list of files preventing worker to exit

        including PENDING as those have not been uploaded/checked
        including UPLOADING as those might fail and go back to PENDING"""
        return list(
            filter(
                lambda x: x[1][UP] in (PENDING, UPLOADING)
                or x[1][CHK] in (PENDING, CHECKING),
                self.zim_files.items(),
            )
        )

    def check_files(self):
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
            self.zim_files[zim_file][CHK] = CHECKED

            # get result of container
            zimcheck_log = get_container_logs(
                self.docker,
                self.checker.name,  # pyright: ignore[reportArgumentType]
            ).strip()
            try:
                zimcheck_result = ujson.loads(zimcheck_log)
            except Exception as exc:
                zimcheck_result = None
                logger.warning(f"Failed to parse zimcheck output: {exc}")
            else:
                zimcheck_log = None

            self.mark_file_checked(
                zim_file,  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
                zimcheck_retcode=self.checker.attrs["State"]["ExitCode"],
                zimcheck_result=zimcheck_result,
                zimcheck_log=zimcheck_log,
                info=get_zim_info(
                    self.task_workdir
                    / zim_file  # pyright: ignore[reportUnknownArgumentType]
                ),
            )
            self.checker.remove()
            self.checker = None

        # start a checker instance
        if (
            self.checker is None
            and self.pending_zim_files(CHK)
            and not self.should_stop
        ):
            try:
                zim_file, _ = self.pending_zim_files(CHK).pop()
            except Exception:
                # no more pending files,
                logger.debug("failed to get ZIM file: pending_zim_files empty")
            else:
                self.start_checker(zim_file)
                self.zim_files[zim_file][CHK] = UPLOADING

    def upload_files(self):
        """manages self.zim_files

        - list files in folder to upload list
        - upload files one by one using dedicated uploader containers"""
        # check files in workdir and update our list of files to upload
        self.refresh_files_list()

        # check if uploader running
        if self.uploader:
            self.uploader.reload()

        if self.uploader and self.uploader.status in RUNNING_STATUSES:
            # still running, nothing to do
            return

        # not running but _was_ running
        if self.uploader:
            # find file
            zim_file = self.uploader.labels[  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                "filename"
            ]
            # get result of container
            if self.uploader.attrs["State"]["ExitCode"] == 0:
                self.zim_files[zim_file][UP] = UPLOADED
                self.mark_file_completed(
                    zim_file,  # pyright: ignore[reportUnknownArgumentType]
                    "uploaded",
                )
            else:
                logger.error(
                    f"ZIM Uploader:: "
                    f"{get_container_logs(self.docker, self.uploader.name)}"  # pyright: ignore[reportArgumentType]
                )
                self.zim_retries[  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                    zim_file
                ] = (
                    self.zim_retries.get(  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                        zim_file,
                        0,  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                    )
                    + 1
                )
                if (
                    self.zim_retries[  # pyright: ignore[reportUnknownMemberType]
                        zim_file
                    ]
                    >= MAX_ZIM_RETRIES
                ):
                    logger.error(f"{zim_file} exhausted retries ({MAX_ZIM_RETRIES})")
                    self.zim_files[zim_file][UP] = FAILED
                    self.mark_file_completed(
                        zim_file,  # pyright: ignore[reportUnknownArgumentType]
                        "failed",
                    )
                else:
                    self.zim_files[zim_file][UP] = PENDING
            self.uploader.remove()
            self.uploader = None

        # start an uploader instance
        if not self.task:
            logger.error("No task to upload files")
            return
        if (
            self.uploader is None
            and self.pending_zim_files(UP)
            and not self.should_stop
        ):
            try:
                zim_file, _ = self.pending_zim_files(UP).pop()
            except Exception:
                # no more pending files,
                logger.debug("failed to get ZIM file: pending_zim_files empty")
            else:
                self.start_uploader(self.task["config"]["warehouse_path"], zim_file)
                self.zim_files[zim_file][UP] = UPLOADING

    def handle_files(self):
        self.upload_files()
        self.check_files()

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
            self.handle_files()

        # scraper is done.
        # submit final progress (especially partialZim property)
        self.submit_scraper_progress()
        # check files so upload can continue
        self.handle_stopped_scraper()

        self.handle_files()  # rescan folder

        # monitor upload/check of files
        while not self.should_stop and (
            self.busy_zim_files
            or self.container_running("uploader")
            or self.container_running("checker")
            or self.container_running("log_uploader")
            or self.container_running("artifacts_uploader")
        ):
            now = getnow()
            if (now - last_check).total_seconds() < SLEEP_INTERVAL:
                self.sleep()
                continue

            last_check = now
            self.handle_files()
            self.check_scraper_log_upload()
            self.check_scraper_artifacts_upload()

        # make sure we submit upload status for last zim and scraper log
        self.handle_files()
        self.check_scraper_log_upload()
        self.check_scraper_artifacts_upload()

        # done with processing, cleaning-up and exiting
        self.shutdown(
            "succeeded"
            if (self.scraper_succeeded and len(self.zim_files) > 0)
            else "failed"
        )
