#!/usr/bin/env python3
"""
Upload zimcheck results (check_details, check_log, check_result) to S3.

This script finds files that have been checked but whose check results
have not been uploaded yet, creates a JSON file with the zimcheck data,
and uploads it to the configured zimcheck_upload_uri.

The JSON file format:
{
    "filename": "name_of_zim_file.zim",
    "info": {...},  # file metadata
    "result": "check_details",  # detailed check results
    "log": "check_log",  # check log output
    "retcode": check_result  # check return code
}
"""

import argparse
import datetime
import json
import logging
import re
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from kiwixstorage import KiwixStorage  # pyright: ignore[reportMissingTypeStubs]
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend import logger
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import (
    ZIMCHECK_RESULTS_EXPIRATION,
    ZIMCHECK_RESULTS_UPLOAD_URI,
)
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.common.upload import rebuild_uri
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import File, Task
from zimfarm_backend.db.tasks import create_or_update_task_file, get_task_file


def get_url_scheme(url: urllib.parse.ParseResult) -> str:
    if url.scheme.startswith("s3+http"):
        return "http"
    # covers both "s3" and "s3+https"
    elif url.scheme.startswith("s3") or url.scheme.startswith("s3+https"):
        return "https"
    else:
        raise ValueError(f"Unsupported URL scheme in: {url}")


def upload_to_s3(
    upload_uri: str,
    json_data: dict[str, Any],
    filename: str,
    expiration_days: int | None,
):
    """Upload the zimcheck JSON data to S3"""
    try:
        uri = urllib.parse.urlparse(upload_uri)
        # Initialize KiwixStorage with the upload URI
        storage = KiwixStorage(rebuild_uri(uri, scheme=get_url_scheme(uri)).geturl())

        # Create a temporary file with the JSON data
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(json_data, temp_file, indent=2)
            temp_file_path = temp_file.name

        try:
            # Upload the file
            with open(temp_file_path, "rb") as f:
                storage.upload_fileobj(  # pyright: ignore[reportUnknownMemberType]
                    fileobj=f,
                    key=filename,
                    meta={
                        "ContentType": "application/json",
                    },
                )
                if expiration_days:
                    storage.set_object_autodelete_on(  # pyright: ignore[reportUnknownMemberType]
                        key=filename,
                        on=getnow() + datetime.timedelta(days=expiration_days),
                    )
            logger.info(f"Successfully uploaded {filename}")
        finally:
            # Clean up the temporary file
            Path(temp_file_path).unlink(missing_ok=True)
    except Exception:
        logger.exception(f"Failed to upload {filename}")
        raise


def upload_zimcheck_results(
    session: OrmSession,
    *,
    upload_uri: str,
    expiration_days: int | None = None,
):
    """Upload zimcheck results for files that have been checked but not uploaded yet."""

    logger.info(f"Using upload URI: {upload_uri}")

    # Find files that have been checked but not uploaded
    rows = session.execute(
        sa.select(File.task_id, File.name)
        .where(
            File.check_result.is_not(None),  # Has been checked
            (
                File.check_details.is_not(None) | (File.check_log.is_not(None))
            ),  # Has details
            File.check_filename.is_(None),  # Results not uploaded yet
        )
        .order_by(File.created_timestamp.desc())
    ).all()

    nb_processed = 0

    for task_id, filename in rows:
        file = get_task_file(session, task_id, filename)
        # Create the JSON payload
        json_data = {
            "filename": file.name,
            "info": file.info,
            "result": file.check_details,
            "log": file.check_log,
            "retcode": file.check_result,
        }
        with session.begin_nested():
            try:
                check_filename = f"{file.info['id']}_zimcheck.json"
                upload_to_s3(upload_uri, json_data, check_filename, expiration_days)
                file = create_or_update_task_file(
                    session,
                    FileCreateUpdateSchema(
                        name=file.name,
                        task_id=file.task_id,
                        check_upload_timestamp=getnow(),
                        check_filename=check_filename,
                        status="check_results_uploaded",
                    ),
                )
                # insert the upload uri and expiration days in the task, to be
                # used in reconstructing the URL
                task = session.scalars(
                    select(Task).where(Task.id == file.task_id)
                ).one()
                task.upload["check"] = {
                    "upload_uri": upload_uri,
                    "expiration": expiration_days,
                }
                flag_modified(task, "upload")

                nb_processed += 1
                logger.info(
                    f"Updated file record: check_filename={check_filename}, "
                    f"check_upload_timestamp={file.check_upload_timestamp}"
                )
            except Exception:
                logger.exception(
                    f"Failed to upload zimcheck results for file {file.name}"
                )
    logger.info(f"Uploaded {nb_processed} zimcheck results to S3")


def main():
    parser = argparse.ArgumentParser(
        description="Upload zimcheck results to S3",
    )
    parser.add_argument(
        "--upload-uri",
        help="S3 upload URI (overrides ZIMCHECK_RESULTS_UPLOAD_URI)",
        default=ZIMCHECK_RESULTS_UPLOAD_URI,
    )

    parser.add_argument(
        "--expiration",
        type=int,
        help="S3 upload expiration in days (overrides ZIMCHECK_RESULTS_EXPIRATION)",
        default=ZIMCHECK_RESULTS_EXPIRATION,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not re.match(r"s3(?:\+https?)?:\/\/", args.upload_uri):
        logger.error("URL must be an S3 URL")
        return

    with Session.begin() as session:
        try:
            upload_zimcheck_results(
                session=session,
                upload_uri=args.upload_uri,
                expiration_days=args.expiration,
            )
        except (KeyboardInterrupt, Exception) as exc:
            logger.error(f"Aborted: {exc!s}")
            pass


if __name__ == "__main__":
    main()
