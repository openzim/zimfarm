#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" SCP/SFTP file uploader for openZIM/Zimfarm

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
import urllib
import logging
import pathlib
import argparse
import tempfile
import datetime
import subprocess

try:
    import humanfriendly
except ImportError:
    humanfriendly = None

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

HOST_KNOW_FILE = pathlib.Path("/etc/ssh/known_hosts")
MARKER_FILE = pathlib.Path("/usr/share/marker")
SCP_BIN_PATH = pathlib.Path(os.getenv("SCP_BIN_PATH", "/usr/bin/scp"))
SFTP_BIN_PATH = pathlib.Path(os.getenv("SFTP_BIN_PATH", "/usr/bin/sftp"))


def now():
    return datetime.datetime.now()


def ack_host_fingerprint(host, port):
    """ run/store ssh-keyscan to prevent need to manually confirm host fingerprint """
    keyscan = subprocess.run(
        ["/usr/bin/ssh-keyscan", "-p", str(port), host], capture_output=True, text=True,
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
    """ transfer a file via SCP and return subprocess """

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
        f"[WIP] uploaded to temp file `{temp_fname}` successfuly. uploading complete marker..."
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
            f"scp failed to transfer upload marker returning {scp.returncode}:: {scp.stdout}"
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
        args=args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
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
        args=args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
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
                "Nothing to upload (destination file bigger or same size as source file)"
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


def rebuild_uri(
    uri, scheme=None, username=None, password=None, hostname=None, port=None, path=None
):
    scheme = scheme or uri.scheme
    username = username or uri.username
    password = password or uri.password
    hostname = hostname or uri.hostname
    port = port or uri.port
    path = path or uri.path
    new_uri = f"{scheme}://"
    if username:
        new_uri += username
    if password:
        new_uri += f":{password}"
    if username or password:
        new_uri += "@"
    new_uri += hostname
    if port:
        new_uri += f":{port}"
    if path:
        new_uri += path
    return urllib.parse.urlparse(new_uri)


def display_stats(filesize, started_on, ended_on=None):
    ended_on = ended_on or now()
    duration = (ended_on - started_on).total_seconds()
    if humanfriendly:
        hfilesize = humanfriendly.format_size(filesize, binary=True)
        hduration = humanfriendly.format_timespan(duration, max_units=2)
        speed = humanfriendly.format_size(filesize / duration)
        msg = f"uploaded {hfilesize} in {hduration} ({speed}/s)"
    else:
        hfilesize = filesize / 2 ** 20  # size in MiB
        speed = filesize / 1000000 / duration  # MB/s
        duration = duration / 60  # in mn
        msg = f"uploaded {hfilesize:.3}MiB in {duration:.1}mn ({speed:.3}MBps)"
    logger.info(f"[stats] {msg}")


def upload_file(
    src_path,
    upload_uri,
    private_key,
    username=None,
    resume=False,
    move=False,
    delete=False,
    compress=False,
    bandwidth=None,
    cipher=None,
):
    try:
        upload_uri = urllib.parse.urlparse(upload_uri)
        pathlib.Path(upload_uri.path)
    except Exception as exc:
        logger.error(f"invalid upload URI: `{upload_uri}` ({exc}).")
        return 1

    # set username in URI if provided and URI has none
    if username and not upload_uri.username:
        upload_uri = rebuild_uri(upload_uri, username=username)

    logger.info(f"Starting upload of {src_path} to {upload_uri.geturl()}")

    method = {"scp": scp_upload_file, "sftp": sftp_upload_file,}.get(upload_uri.scheme)

    if not method:
        logger.critical(f"URI scheme not supported: {upload_uri.scheme}")
        return 1

    if upload_uri.scheme == "scp" and resume:
        logger.warning("--resume not supported via SCP. Will upload from scratch.")

    return method(
        src_path,
        upload_uri,
        src_path.stat().st_size,
        private_key,
        resume,
        move,
        delete,
        compress,
        bandwidth,
        cipher,
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
        required=not bool(os.getenv("RSA_KEY", "/etc/ssh/keys/id_rsa")),
        default=os.getenv("RSA_KEY", "/etc/ssh/keys/id_rsa"),
    )

    parser.add_argument(
        "--username", help="username to authenticate to warehouse (if not in URI)",
    )

    parser.add_argument(
        "--resume",
        help="whether to continue uploading existing remote file instead of overriding (SFTP only)",
        action="store_true",
        default=False,
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
        "--bandwidth", help="limit bandwidth used for transfer. In Kbit/s.", type=int,
    )

    parser.add_argument(
        "--cipher", help="Cipher to use with SSH.", default="aes128-ctr"
    )

    parser.add_argument(
        "--debug",
        help="change logging level to DEBUG",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    # fail early if source file is not readable
    src_path = pathlib.Path(args.src_path).resolve()
    if (
        not src_path.exists()
        or not src_path.is_file()
        or not os.access(src_path, os.R_OK)
    ):
        logger.error(f"source file ({src_path}) doesn't exist or is not readable.")
        sys.exit(1)

    # fail early if private key is not readable
    private_key = pathlib.Path(args.private_key).resolve()
    if (
        not private_key.exists()
        or not private_key.is_file()
        or not os.access(private_key, os.R_OK)
    ):
        logger.error(
            f"private RSA key file ({private_key}) doesn't exist or is not readable."
        )
        sys.exit(1)

    # make sur upload-uri is correct (trailing slash)
    try:
        url = urllib.parse.urlparse(args.upload_uri)
    except Exception as exc:
        logger.error(f"invalid upload URI: `{args.upload_uri}` ({exc}).")
        sys.exit(1)
    else:
        if not url.path.endswith("/") and not pathlib.Path(url.path).suffix:
            logger.error(
                f"/!\\ your upload_uri doesn't end with a slash and has no file extension: `{args.upload_uri}`."
            )
            sys.exit(1)

    ack_host_fingerprint(url.hostname, url.port)

    # running upload
    sys.exit(
        upload_file(
            src_path=src_path,
            upload_uri=args.upload_uri,
            username=args.username,
            private_key=private_key,
            resume=args.resume,
            move=args.move,
            delete=args.delete,
            compress=args.compress,
            bandwidth=args.bandwidth,
            cipher=args.cipher,
        )
    )


if __name__ == "__main__":
    main()
