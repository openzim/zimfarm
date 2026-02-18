#!/usr/bin/env python3

"""
Script to update files in the database by renaming metadata keys that start with
'Illustration_' to include '@1' suffix.
"""

import argparse

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import File


def update_files_illustration_metadata() -> None:
    """
    Update files in the database to rename Illustration_ keys in metadata.
    """
    with Session.begin() as session:
        for file in session.execute(select(File)).scalars():
            if not file.info:
                logger.warning(f"{file.name} does not have any zim info")
                continue

            metadata = file.info.get("metadata", {})
            if not metadata:
                logger.warning(f"{file.name} does not have any zim metadata")
                continue

            illustration_keys = [
                key for key in metadata.keys() if key.startswith("Illustration_")
            ]

            if not illustration_keys:
                logger.warning(f"{file.name} metadata does not have illustration keys.")
                continue

            for illustration_key in illustration_keys:
                logger.info(
                    f"Renaming {illustration_key} metadata for {file.name} "
                    f"({file.id})..."
                )
                value = file.info["metadata"][illustration_key]
                suffix = illustration_key[len("Illustration_") :]
                new_key = f"Illustration_{suffix}@1"

                del file.info["metadata"][illustration_key]
                file.info["metadata"][new_key] = value
                flag_modified(file, "info")
                logger.info(f"Renamed '{illustration_key}' to '{new_key}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update file metadata to rename illustration_ keys with @1 suffix",
    )

    args = parser.parse_args()

    update_files_illustration_metadata()
