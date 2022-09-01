#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" SCP/SFTP/S3 file uploader for openZIM/Zimfarm

    manual tests lists (for each method):
        - with username in URI
        - with username in param
        - not specifying target name
        - specifying target name
        - --move not specifying target name
        - --move specifying target name
        - with --cipher
        - without --cipher
        - --delete
        - --compress
        - --bandwidth
"""

import os
import sys
import time
import urllib
import signal
import logging
import pathlib
import argparse
import tempfile
import datetime
import subprocess

from kiwixstorage import KiwixStorage, FileTransferHook

try:
    import humanfriendly
except ImportError:
    humanfriendly = None

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

HOST_KNOW_FILE = (
    pathlib.Path(os.getenv("HOST_KNOW_FILE", "~/.ssh/known_hosts"))
    .expanduser()
    .resolve()
)
MARKER_FILE = pathlib.Path(os.getenv("MARKER_FILE", "/usr/share/marker"))
SCP_BIN_PATH = pathlib.Path(os.getenv("SCP_BIN_PATH", "/usr/bin/scp"))
SFTP_BIN_PATH = pathlib.Path(os.getenv("SFTP_BIN_PATH", "/usr/bin/sftp"))


def now():
    return datetime.datetime.now()


def ack_host_fingerprint(host, port):
    """run/store ssh-keyscan to prevent need to manually confirm host fingerprint"""
    keyscan = subprocess.run(
        ["/usr/bin/ssh-keyscan", "-p", str(port), host],
        capture_output=True,
        text=True,
    )
    if keyscan.returncode != 0:
        logger.error(f"unable to get remote host ({host}:{port}) public key")
        sys.exit(1)

    with open(HOST_KNOW_FILE, "w") as keyscan_output:
        keyscan_output.write(keyscan.stdout)
        keyscan_output.seek(0)


def remove_source_file(src_path):
    logger.info("removing source file…")
    try:
        src_path.unlink()
    except Exception as exc:
        logger.error(f":: failed to remove ZIM file: {exc}")
    else:
        logger.info(":: success.")


def scp_actual_upload(private_key, source_path, dest_uri, cipher, compress, bandwidth):
    """transfer a file via SCP and return subprocess"""

    args = [
        str(SCP_BIN_PATH),
        "-i",
        str(private_key),
        "-B",  # batch mode
        "-q",  # quiet mode
        "-o",
        f"GlobalKnownHostsFile {HOST_KNOW_FILE}",
    ]

    if cipher:
        args += ["-c", cipher]

    if compress:
        args += ["-C"]

    if bandwidth:
        args += ["-l", str(bandwidth)]

    args += [str(source_path), dest_uri.geturl()]

    logger.info("Executing: {args}".format(args=" ".join(args)))

    return subprocess.run(
        args=args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )


def scp_upload_file(
    src_path,
    upload_uri,
    filesize,
    private_key,
    resume=False,
    move=False,
    delete=False,
    compress=False,
    bandwidth=None,
    cipher=None,
    delete_after=None,
):
    # directly uploading final file to final destination
    if not move:
        started_on = now()
        scp = scp_actual_upload(
            private_key, src_path, upload_uri, cipher, compress, bandwidth
        )
        ended_on = now()

        if scp.returncode == 0:
            logger.info("Uploader ran successfuly.")
            if delete:
                remove_source_file(src_path)
            display_stats(filesize, started_on, ended_on)
        else:
            logger.error(f"scp failed returning {scp.returncode}:: {scp.stdout}")

        return scp.returncode

    # uploading file in two steps
    # - uploading to temporary name
    # - uploading an upload-complete marker aside
    if upload_uri.path.endswith("/"):
        real_fname = src_path.name
        dest_folder = upload_uri.path
    else:
        uri_path = pathlib.Path(upload_uri.path)
        real_fname = uri_path.name
        dest_folder = f"{uri_path.parent}/"

    temp_fname = f"{real_fname}.tmp"
    dest_path = f"{dest_folder}{temp_fname}"
    marker_dest_path = f"{dest_folder}{real_fname}.complete"

    started_on = now()
    scp = scp_actual_upload(
        private_key,
        src_path,
        rebuild_uri(upload_uri, path=dest_path),
        cipher,
        compress,
        bandwidth,
    )
    ended_on = now()

    if scp.returncode != 0:
        logger.critical(f"scp failed returning {scp.returncode}:: {scp.stdout}")
        return scp.returncode

    logger.info(
        f"[WIP] uploaded to temp file `{temp_fname}` successfuly. "
        f"uploading complete marker..."
    )
    if delete:
        remove_source_file(src_path)

    scp = scp_actual_upload(
        private_key,
        MARKER_FILE,
        rebuild_uri(upload_uri, path=marker_dest_path),
        cipher,
        compress,
        bandwidth,
    )

    if scp.returncode == 0:
        logger.info("Uploader ran successfuly.")
    else:
        logger.warning(
            f"scp failed to transfer upload marker "
            f"returning {scp.returncode}:: {scp.stdout}"
        )
        logger.warning(
            "actual file transferred properly though. You'd need to move it manually."
        )
    display_stats(filesize, started_on, ended_on)

    return scp.returncode


def get_batch_file(commands):
    command_content = "\n".join(commands)
    logger.debug(f"SFTP commands:\n{command_content}---")
    batch_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    batch_file.write(command_content)
    batch_file.close()
    return batch_file.name


def sftp_remote_file_exists(private_key, sftp_uri, fname):
    args = [
        str(SFTP_BIN_PATH),
        "-i",
        str(private_key),
        "-b",
        get_batch_file([f"ls -n {fname}"]),
        "-o",
        f"GlobalKnownHostsFile {HOST_KNOW_FILE}",
        sftp_uri.geturl(),
    ]

    logger.info("Executing: {args}".format(args=" ".join(args)))

    sftp = subprocess.run(
        args=args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    last_line = sftp.stdout.strip().split("\n")[-1]
    if not last_line.endswith(fname) or last_line.startswith("sftp"):
        return False

    try:
        remote_size = int(last_line.split()[4])
    except Exception:
        return False

    return remote_size or sftp.returncode == 0


def sftp_actual_upload(
    private_key, source_path, sftp_uri, commands, cipher, compress, bandwidth
):
    args = [
        str(SFTP_BIN_PATH),
        "-i",
        str(private_key),
        "-b",
        get_batch_file(commands),
        "-o",
        f"GlobalKnownHostsFile {HOST_KNOW_FILE}",
    ]

    if cipher:
        args += ["-c", cipher]

    if compress:
        args += ["-C"]

    if bandwidth:
        args += ["-l", str(bandwidth)]

    args += [sftp_uri.geturl()]

    logger.info("Executing: {args}".format(args=" ".join(args)))

    return subprocess.run(
        args=args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def sftp_upload_file(
    src_path,
    upload_uri,
    filesize,
    private_key,
    resume=False,
    move=False,
    delete=False,
    compress=False,
    bandwidth=None,
    cipher=None,
    delete_after=None,
):
    # we need to reconstruct the url but without an ending filename
    if not upload_uri.path.endswith("/"):
        uri_path = pathlib.Path(upload_uri.path)
        final_fname = uri_path.name
        sftp_uri = rebuild_uri(upload_uri, path=f"{uri_path.parent}/")
    else:
        final_fname = src_path.name
        sftp_uri = upload_uri

    put_cmd = "put"  # default to overwritting
    if resume:
        # check if there's already a matching file on the remte
        existing_size = sftp_remote_file_exists(private_key, sftp_uri, final_fname)
        # if source and destination filesizes match, return as sftp would fail
        if existing_size >= filesize:
            logger.info(
                "Nothing to upload "
                "(destination file bigger or same size as source file)"
            )
            return 0
        # there's a different size file on destination, let's overwrite
        if existing_size:
            put_cmd = "reput"  # change to APPEND mode
            filesize = filesize - existing_size  # used for stats

    if move:
        temp_fname = f"{final_fname}.tmp"
        commands = [
            f"{put_cmd} {src_path} {temp_fname}",
            f"rename {temp_fname} {final_fname}",
            "bye",
        ]
    else:
        commands = [f"{put_cmd} {src_path} {final_fname}", "bye"]

    started_on = now()
    sftp = sftp_actual_upload(
        private_key, src_path, sftp_uri, commands, cipher, compress, bandwidth
    )
    ended_on = now()

    if sftp.returncode == 0:
        logger.info("Uploader ran successfuly.")
        display_stats(filesize, started_on, ended_on)
        if delete:
            remove_source_file(src_path)
    else:
        logger.error(f"sftp failed returning {sftp.returncode}:: {sftp.stdout}")

    return sftp.returncode


def s3_upload_file(
    src_path,
    upload_uri,
    filesize,
    private_key,  # not used
    resume=False,  # not supported
    move=False,  # not relevant
    delete=False,
    compress=False,  # not relevant
    bandwidth=None,  # not supported
    cipher=None,  # not relevant
    delete_after=None,  # nb of days to expire upload file after
):
    started_on = now()
    s3_storage = KiwixStorage(rebuild_uri(upload_uri, scheme="https").geturl())
    logger.debug(f"S3 initialized for {s3_storage.url.netloc}/{s3_storage.bucket_name}")

    key = upload_uri.path[1:]
    if upload_uri.path.endswith("/"):
        key += src_path.name

    try:
        logger.info(f"Uploading to {key}")
        hook = FileTransferHook(filename=src_path)
        s3_storage.upload_file(fpath=str(src_path), key=key, Callback=hook)
        print("", flush=True)
    except Exception as exc:
        # as there is no resume, uploading to existing URL will result in DELETE+UPLOAD
        # if credentials doesn't allow DELETE or if there is an unsatisfied
        # retention, will raise PermissionError
        logger.error(f"uploader failed: {exc}")
        logger.exception(exc)
        return 1
    ended_on = now()
    logger.info("uploader ran successfuly.")

    # setting autodelete
    if delete_after is not None:
        try:
            # set expiration after bucket's min retention.
            # bucket retention is 1d minumum.
            # can be configured to loger value.
            # if expiration before bucket min retention, raises 400 Bad Request
            # on compliance
            expire_on = (
                datetime.datetime.now()
                + datetime.timedelta(days=delete_after or 1)
                # adding 1mn to prevent clash with bucket's equivalent min retention
                + datetime.timedelta(seconds=60)
            )
            logger.info(f"Setting autodelete to {expire_on}")
            s3_storage.set_object_autodelete_on(key=key, on=expire_on)
        except Exception as exc:
            logger.error(f"Failed to set autodelete: {exc}")
            logger.exception(exc)

    if delete:
        remove_source_file(src_path)
    display_stats(filesize, started_on, ended_on)

    return 0


def rebuild_uri(
    uri,
    scheme=None,
    username=None,
    password=None,
    hostname=None,
    port=None,
    path=None,
    params=None,
    query=None,
    fragment=None,
):
    scheme = scheme or uri.scheme
    username = username or uri.username
    password = password or uri.password
    hostname = hostname or uri.hostname
    port = port or uri.port
    path = path or uri.path
    netloc = ""
    if username:
        netloc += username
    if password:
        netloc += f":{password}"
    if username or password:
        netloc += "@"
    netloc += hostname
    if port:
        netloc += f":{port}"
    params = params or uri.params
    query = query or uri.query
    fragment = fragment or uri.fragment
    return urllib.parse.urlparse(
        urllib.parse.urlunparse([scheme, netloc, path, fragment, query, fragment])
    )


def display_stats(filesize, started_on, ended_on=None):
    ended_on = ended_on or now()
    duration = (ended_on - started_on).total_seconds()
    if humanfriendly:
        hfilesize = humanfriendly.format_size(filesize, binary=True)
        hduration = humanfriendly.format_timespan(duration, max_units=2)
        speed = humanfriendly.format_size(filesize / duration)
        msg = f"uploaded {hfilesize} in {hduration} ({speed}/s)"
    else:
        hfilesize = filesize / 2**20  # size in MiB
        speed = filesize / 1000000 / duration  # MB/s
        duration = duration / 60  # in mn
        msg = f"uploaded {hfilesize:.3}MiB in {duration:.1}mn ({speed:.3}MBps)"
    logger.info(f"[stats] {msg}")


def watched_upload(delay, method, **kwargs):
    str_delay = humanfriendly.format_timespan(delay) if humanfriendly else f"{delay}s"
    logger.info(f"... watching file until {str_delay} after last modification")

    class ExitCatcher:
        def __init__(self):
            self.requested = False
            for name in ["TERM", "INT", "QUIT"]:
                signal.signal(getattr(signal, f"SIG{name}"), self.on_exit)

        def on_exit(self, signum, frame):
            self.requested = True
            logger.info(f"received signal {signal.strsignal(signum)}, graceful exit.")

    exit_catcher = ExitCatcher()
    last_change = datetime.datetime.fromtimestamp(kwargs["src_path"].stat().st_mtime)
    last_upload, retries = None, 10

    while (
        # make sure we upload it at least once
        not last_upload
        # delay without change has not expired
        or datetime.datetime.now() - datetime.timedelta(seconds=delay) < last_change
    ):

        # file has changed (or initial), we need to upload
        if not last_upload or last_upload < last_change:
            started_on = datetime.datetime.now()
            kwargs["filesize"] = kwargs["src_path"].stat().st_size
            returncode = method(**kwargs)
            if returncode != 0:
                retries -= 1
                if retries <= 0:
                    return returncode
            else:
                if not last_upload:  # this was first run
                    kwargs["resume"] = True
                last_upload = started_on

        if exit_catcher.requested:
            break

        # nb of seconds to sleep between modtime checks
        time.sleep(1)

        # refresh modification time
        last_change = datetime.datetime.fromtimestamp(
            kwargs["src_path"].stat().st_mtime
        )
    if not exit_catcher.requested:
        logger.info(f"File last modified on {last_change}. Delay expired.")


def upload_file(
    src_path,
    upload_uri,
    private_key,
    username=None,
    resume=False,
    watch=None,
    move=False,
    delete=False,
    compress=False,
    bandwidth=None,
    cipher=None,
    delete_after=None,
):
    try:
        upload_uri = urllib.parse.urlparse(upload_uri)
        pathlib.Path(upload_uri.path)
    except Exception as exc:
        logger.error(f"invalid upload URI: `{upload_uri}` ({exc}).")
        return 1

    # set username in URI if provided and URI has none
    if upload_uri.scheme in ("scp", "sftp") and username and not upload_uri.username:
        upload_uri = rebuild_uri(upload_uri, username=username)

    if upload_uri.scheme == "s3":
        params = urllib.parse.parse_qs(upload_uri.query)
        if "secretAccessKey" in params.keys():
            params["secretAccessKey"] = ["xxxxx"]
        safe_upload_uri = rebuild_uri(
            upload_uri, query=urllib.parse.urlencode(params, doseq=True)
        ).geturl()
    else:
        safe_upload_uri = upload_uri.geturl()

    logger.info(f"Starting upload of {src_path} to {safe_upload_uri}")

    method = {
        "scp": scp_upload_file,
        "sftp": sftp_upload_file,
        "s3": s3_upload_file,
    }.get(upload_uri.scheme)

    if not method:
        logger.critical(f"URI scheme not supported: {upload_uri.scheme}")
        return 1

    if upload_uri.scheme in ("s3", "scp") and resume:
        logger.warning("--resume not supported via SCP/S3. Will upload from scratch.")

    if upload_uri.scheme != "s3" and delete_after:
        logger.warning("--delete-after only supported on S3/Wasabi.")

    kwargs = {
        "src_path": src_path,
        "upload_uri": upload_uri,
        "filesize": src_path.stat().st_size,
        "private_key": private_key,
        "resume": resume,
        "move": move,
        "delete": delete,
        "compress": compress,
        "bandwidth": bandwidth,
        "cipher": cipher,
        "delete_after": delete_after,
    }

    if watch:
        try:
            # without humanfriendly, watch is considered to be in seconds
            watch = int(humanfriendly.parse_timespan(watch) if humanfriendly else watch)
        except Exception as exc:
            logger.critical(f"--watch delay ({watch}) not correct: {exc}")
            return 1
        return watched_upload(watch, method, **kwargs)

    return method(**kwargs)


def check_and_upload_file(
    src_path,
    upload_uri,
    private_key,
    username=None,
    resume=False,
    watch=None,
    move=False,
    delete=False,
    compress=False,
    bandwidth=None,
    cipher=None,
    delete_after=None,
):
    """checks inputs and uploads file, returning 0 on success"""

    # fail early if source file is not readable
    src_path = pathlib.Path(src_path).expanduser().resolve()
    if (
        not src_path.exists()
        or not src_path.is_file()
        or not os.access(src_path, os.R_OK)
    ):
        logger.error(f"source file ({src_path}) doesn't exist or is not readable.")
        return 1

    # make sur upload-uri is correct (trailing slash)
    try:
        url = urllib.parse.urlparse(upload_uri)
        if not url.scheme or not url.netloc:
            raise ValueError("missing URL component")
    except Exception as exc:
        logger.error(f"invalid upload URI: `{upload_uri}` ({exc}).")
        return 1
    else:
        if not url.path.endswith("/") and not pathlib.Path(url.path).suffix:
            logger.error(
                f"/!\\ your upload_uri doesn't end with a slash "
                f"and has no file extension: `{upload_uri}`."
            )
            return 1

    if url.scheme in ("scp", "sftp"):
        # fail early if private key is not readable
        private_key = pathlib.Path(private_key).expanduser().resolve()
        if (
            not private_key.exists()
            or not private_key.is_file()
            or not os.access(private_key, os.R_OK)
        ):
            logger.error(
                f"private RSA key file ({private_key}) doesn't exist "
                f"or is not readable."
            )
            return 1

        ack_host_fingerprint(url.hostname, url.port)
    else:
        private_key = None

    # running upload
    return upload_file(
        src_path=src_path,
        upload_uri=upload_uri,
        private_key=private_key,
        username=username,
        resume=resume,
        watch=watch,
        move=move,
        delete=delete,
        compress=compress,
        bandwidth=bandwidth,
        cipher=cipher,
        delete_after=delete_after,
    )


def main():
    parser = argparse.ArgumentParser(prog="uploader")

    parser.add_argument(
        "--file",
        help="absolute path to source file to upload",
        required=True,
        dest="src_path",
    )

    parser.add_argument(
        "--upload-uri",
        help="upload URI to upload to (folder, trailing-slash)",
        required=True,
        dest="upload_uri",
    )

    parser.add_argument(
        "--key",
        help="path to RSA private key",
        dest="private_key",
        required=False,
        default=os.getenv("RSA_KEY", "/etc/ssh/keys/id_rsa"),
    )

    parser.add_argument(
        "--username",
        help="username to authenticate to warehouse (if not in URI)",
    )

    parser.add_argument(
        "--resume",
        help="whether to continue uploading existing remote file instead "
        "of overriding (SFTP only)",
        action="store_true",
        default=False,
    )

    # format: https://humanfriendly.readthedocs.io/en/latest/api.html
    # humanfriendly.parse_timespan
    parser.add_argument(
        "--watch",
        help="Keep uploading until file has not been changed "
        "for that period of time (ex. 10s 1m 2h 3d)",
        action="store",
    )

    parser.add_argument(
        "--move",
        help="whether to upload to a temp location and move to final one on success",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--delete",
        help="whether to delete source file upon success",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--compress",
        help="whether to enable ssh compression on transfer (good for text)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--bandwidth",
        help="limit bandwidth used for transfer. In Kbit/s.",
        type=int,
    )

    parser.add_argument(
        "--cipher", help="Cipher to use with SSH.", default="aes128-ctr"
    )

    parser.add_argument(
        "--delete-after",
        help="nb of days after which to autodelete "
        "(Wasabi/S3-only, bucket must support it)",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--debug",
        help="change logging level to DEBUG",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    sys.exit(
        check_and_upload_file(
            src_path=args.src_path,
            upload_uri=args.upload_uri,
            username=args.username,
            private_key=args.private_key,
            resume=args.resume,
            watch=args.watch,
            move=args.move,
            delete=args.delete,
            compress=args.compress,
            bandwidth=args.bandwidth,
            cipher=args.cipher,
            delete_after=args.delete_after,
        )
    )


if __name__ == "__main__":
    main()
