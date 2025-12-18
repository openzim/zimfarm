#!/usr/bin/env python3

import hashlib
from typing import Literal

import requests
from pydantic import AnyUrl
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common.constants import (
    BLOB_PRIVATE_STORAGE_URL,
    BLOB_PUBLIC_STORAGE_URL,
    BLOB_STORAGE_PASSWORD,
    BLOB_STORAGE_USERNAME,
    REQUESTS_TIMEOUT,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import ScheduleConfigSchema
from zimfarm_backend.common.schemas.offliners.transformers import (
    generate_blob_name_uuid,
)
from zimfarm_backend.common.schemas.orms import CreateBlobSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.blob import create_or_update_blob
from zimfarm_backend.db.models import Schedule
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
)


class BlobFlag(BaseModel):
    flag_name: str
    kind: Literal["image", "css", "html", "txt"]


FLAG_MAPPINGS: dict[str, list[BlobFlag]] = {
    "devdocs": [BlobFlag(flag_name="logo_format", kind="image")],
    "freecodecamp": [BlobFlag(flag_name="illustration", kind="image")],
    "ifixit": [BlobFlag(flag_name="icon", kind="image")],
    "kolibri": [
        BlobFlag(flag_name="favicon", kind="image"),
        BlobFlag(flag_name="css", kind="css"),
    ],
    "mindtouch": [BlobFlag(flag_name="illustration_url", kind="image")],
    "mwoffliner": [
        BlobFlag(flag_name="customZimFavicon", kind="image"),
        BlobFlag(flag_name="articleList", kind="txt"),
        BlobFlag(flag_name="articleListToIgnore", kind="txt"),
    ],
    "nautilus": [
        BlobFlag(flag_name="main_logo", kind="image"),
        BlobFlag(flag_name="secondary_logo", kind="image"),
        BlobFlag(flag_name="favicon", kind="image"),
    ],
    "openedx": [BlobFlag(flag_name="favicon_url", kind="image")],
    "sotoki": [BlobFlag(flag_name="favicon", kind="image")],
    "youtube": [
        BlobFlag(flag_name="profile", kind="image"),
        BlobFlag(flag_name="banner", kind="image"),
    ],
    "zimit": [
        BlobFlag(flag_name="favicon", kind="image"),
        BlobFlag(flag_name="custom_css", kind="css"),
    ],
}


def delete_blob(old_url: str) -> None:
    """Delete a blob from storage."""
    try:
        response = requests.request(
            "DELETE",
            old_url,
            timeout=REQUESTS_TIMEOUT,
            auth=(BLOB_STORAGE_USERNAME, BLOB_STORAGE_PASSWORD),
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"Failed to delete file at {old_url}, exc: {exc!s}")
    logger.info(f"Deleted file at '{old_url}'")


def copy_blob(old_url: str, flag_name: str, kind: str) -> CreateBlobSchema | None:
    """Fetch blob from old_url, compute checksum, and copy to new location"""
    try:
        fetch_response = requests.get(
            old_url,
            timeout=REQUESTS_TIMEOUT,
            auth=(BLOB_STORAGE_USERNAME, BLOB_STORAGE_PASSWORD),
        )
        fetch_response.raise_for_status()
        blob_data = fetch_response.content
    except Exception as exc:
        logger.warning(f"Failed to fetch {old_url}, exc: {exc!s}")
        return None

    checksum = hashlib.sha256(blob_data).hexdigest()

    filename = generate_blob_name_uuid(kind)
    new_private_url = f"{BLOB_PRIVATE_STORAGE_URL}/{filename}"
    new_public_url = f"{BLOB_PUBLIC_STORAGE_URL}/{filename}"

    # Copy blob to new destination with overwrite set to F. This would raise an error
    # if a file already exists at the location. While this shouldn't happen, it can
    # be a safety net on the chance that it does happen. To overwrite, set to T.
    headers = {"Destination": new_private_url, "Overwrite": "F"}

    try:
        copy_response = requests.request(
            "COPY",
            old_url,
            headers=headers,
            timeout=REQUESTS_TIMEOUT,
            auth=(BLOB_STORAGE_USERNAME, BLOB_STORAGE_PASSWORD),
        )
        copy_response.raise_for_status()
    except Exception as exc:
        logger.warning(f"Failed to move {old_url} to {new_private_url}, exc: {exc!s}")
        return None

    return CreateBlobSchema(
        flag_name=flag_name,
        kind=kind,
        url=AnyUrl(new_public_url),
        checksum=checksum,
    )


def main():
    # list of blob urls to delete after copying them to new locations
    blobs_to_delete: set[str] = set()
    with Session.begin() as session:
        for offliner_id, flag_mappings in FLAG_MAPPINGS.items():
            logger.info(f"Processing offliner: {offliner_id}")
            offliner = get_offliner(session, offliner_id)

            for schedule in session.execute(
                select(Schedule)
                .where(
                    Schedule.config["offliner"]["offliner_id"].astext == offliner_id,
                )
                .options(selectinload(Schedule.offliner_definition))
            ).scalars():
                logger.info(f"Processing schedule {schedule.name} blobs...")
                offliner_definition = create_offliner_definition_schema(
                    schedule.offliner_definition
                )
                schedule_config = ScheduleConfigSchema.model_validate(
                    {
                        **schedule.config,
                        "offliner": create_offliner_instance(
                            offliner=offliner,
                            offliner_definition=offliner_definition,
                            data=schedule.config["offliner"],
                            skip_validation=True,
                        ),
                    },
                    context={"skip_validation": True},
                )
                for flag in flag_mappings:
                    old_url = getattr(schedule_config.offliner, flag.flag_name)
                    if not old_url:
                        continue

                    if not old_url.startswith("http"):
                        logger.warning(
                            f"Schedule '{schedule.name}' flag '{flag.flag_name}' is "
                            "not a valid URL"
                        )
                        continue

                    blob_schema = copy_blob(
                        old_url,
                        flag.flag_name,
                        flag.kind,
                    )
                    if not blob_schema:
                        continue

                    create_or_update_blob(
                        session, schedule_id=schedule.id, request=blob_schema
                    )
                    setattr(
                        schedule_config.offliner, flag.flag_name, str(blob_schema.url)
                    )
                    schedule.config = schedule_config.model_dump(
                        mode="json", context={"show_secrets": True}
                    )
                    logger.info(
                        f"Updated schedule '{schedule.name}' flag '{flag.flag_name} "
                        f"to '{blob_schema.url!s}'"
                    )
                    blobs_to_delete.add(old_url)

    logger.info("Deleting old blobs...")
    for blob_url in blobs_to_delete:
        delete_blob(blob_url)

    logger.info("FINISH!")


if __name__ == "__main__":
    main()
