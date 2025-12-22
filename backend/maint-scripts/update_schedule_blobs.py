#!/usr/bin/env python3

# ruff: noqa: T201

import argparse
import hashlib
import re
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
from zimfarm_backend.db.models import Blob, Schedule
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
)


class BlobFlag(BaseModel):
    flag_name: str
    kind: Literal["image", "css", "html", "txt"]


class UnavailableAsset(BaseModel):
    schedule: str
    flag: str
    url: str
    error: str


class FilterRule(BaseModel):
    """Filter rule to exclude certain schedule/flag combinations from migration"""

    schedule_pattern: str
    flag_name: str

    def matches(self, schedule_name: str, flag_name: str) -> bool:
        """Check if this rule matches the given schedule and flag"""
        schedule_match = bool(re.search(self.schedule_pattern, schedule_name))
        flag_match = flag_name == self.flag_name
        return schedule_match and flag_match


FLAG_MAPPINGS: dict[str, list[BlobFlag]] = {
    "devdocs": [BlobFlag(flag_name="logo_format", kind="image")],
    "freecodecamp": [BlobFlag(flag_name="illustration", kind="image")],
    "ifixit": [BlobFlag(flag_name="icon", kind="image")],
    "kolibri": [
        BlobFlag(flag_name="favicon", kind="image"),
        BlobFlag(flag_name="css", kind="css"),
        BlobFlag(flag_name="about", kind="html"),
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
        BlobFlag(flag_name="about", kind="html"),
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


def upload_blob(url: str, flag_name: str, kind: str) -> CreateBlobSchema | None:
    """
    Download blob from external url, compute blob checksum, and upload to blob storage
    """
    if "wikimedia.org" in url or "wikipedia.org" in url:
        headers = {
            "User-Agent": (
                "zimfarm/2.0 (https://github.com/openzim/zimfarm; "
                f"contact+crawl@kiwix.org) requests/{requests.__version__}"
            )
        }
    else:
        headers = None
    try:
        fetch_response = requests.get(url, timeout=REQUESTS_TIMEOUT, headers=headers)
        fetch_response.raise_for_status()
        blob_data = fetch_response.content
    except Exception as exc:
        logger.warning(f"Failed to fetch {url}, exc: {exc!s}")
        raise

    checksum = hashlib.sha256(blob_data).hexdigest()

    filename = generate_blob_name_uuid(kind)
    new_private_url = f"{BLOB_PRIVATE_STORAGE_URL}/{filename}"
    new_public_url = f"{BLOB_PUBLIC_STORAGE_URL}/{filename}"

    # Upload blob to new destination
    try:
        upload_response = requests.put(
            new_private_url,
            data=blob_data,
            timeout=REQUESTS_TIMEOUT,
            auth=(BLOB_STORAGE_USERNAME, BLOB_STORAGE_PASSWORD),
        )
        upload_response.raise_for_status()
    except Exception as exc:
        logger.warning(f"Failed to upload to {new_private_url}, exc: {exc!s}")
        raise

    return CreateBlobSchema(
        flag_name=flag_name,
        kind=kind,
        url=AnyUrl(new_public_url),
        checksum=checksum,
        comments=f"Original URL: {url}",
    )


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
        raise

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
        raise

    return CreateBlobSchema(
        flag_name=flag_name,
        kind=kind,
        url=AnyUrl(new_public_url),
        checksum=checksum,
    )


def is_blob_storage_url(url: str) -> bool:
    """Check if URL is blob storage (same domain but different path)"""
    return url.startswith(BLOB_PRIVATE_STORAGE_URL.rsplit("/", 1)[0])


def generate_markdown_report(unavailable_assets: list[UnavailableAsset]) -> str:
    """Generate a markdown report of unavailable assets ready for GitHub issue"""
    if not unavailable_assets:
        return "## Migration Report\n\nAll assets migrated successfully!"

    report_lines = [
        "## Unavailable Assets Report",
        "",
        "The following assets could not be migrated and require manual fixing:",
        "",
        "| Schedule | Flag | URL | Error |",
        "|----------|------|-----|-------|",
    ]

    for asset in unavailable_assets:
        # Escape pipe characters in fields for markdown table
        schedule = asset.schedule.replace("|", "\\|")
        flag = asset.flag.replace("|", "\\|")
        url = asset.url.replace("|", "\\|")
        error = asset.error.replace("|", "\\|")
        report_lines.append(f"| {schedule} | {flag} | {url} | {error} |")

    report_lines.extend(
        ["", f"**Total unavailable assets:** {len(unavailable_assets)}"]
    )

    return "\n".join(report_lines)


def main(*, dry_run: bool = False, filter_rules: list[FilterRule] | None = None):
    # list of blob urls to delete after copying them to new locations
    blobs_to_delete: set[str] = set()
    unavailable_assets: list[UnavailableAsset] = []
    total_assets_migrated = 0
    total_assets_skipped = 0
    total_assets_filtered = 0

    if filter_rules is None:
        filter_rules = []

    def should_filter(schedule_name: str, flag_name: str) -> bool:
        """Check if schedule/flag combination should be filtered out"""
        return any(rule.matches(schedule_name, flag_name) for rule in filter_rules)

    for offliner_id, flag_mappings in FLAG_MAPPINGS.items():
        logger.info(f"Processing offliner: {offliner_id}")

        with Session.begin() as session:
            offliner = get_offliner(session, offliner_id)

            schedules = session.execute(
                select(Schedule)
                .where(
                    Schedule.config["offliner"]["offliner_id"].astext == offliner_id,
                )
                .options(selectinload(Schedule.offliner_definition))
            ).scalars()

            for schedule in schedules:
                logger.info(f"Processing schedule {schedule.name}...")
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
                            f"Schedule '{schedule.name}' flag "
                            f"'{flag.flag_name}' is not a valid URL, skipping"
                        )
                        continue

                    # Check if this schedule/flag combination should be filtered
                    if should_filter(schedule.name, flag.flag_name):
                        logger.info(
                            f"🚫 Filtered schedule '{schedule.name}' flag "
                            f"'{flag.flag_name}' (matches filter rule)"
                        )
                        total_assets_filtered += 1
                        continue

                    # Check if blob with URL for this schedule already exists
                    existing_blob = session.scalars(
                        select(Blob)
                        .where(Blob.url == old_url, Blob.schedule_id == schedule.id)
                        .limit(1)
                    ).all()

                    if existing_blob:
                        logger.info(
                            f"Schedule '{schedule.name}' flag '{flag.flag_name}' "
                            "already has blob entry, skipping"
                        )
                        total_assets_skipped += 1
                        continue

                    if dry_run:
                        total_assets_migrated += 1
                        logger.info(
                            f"✅ Migrated schedule '{schedule.name}' flag "
                            f"'{flag.flag_name}' to "
                            f"'{BLOB_PUBLIC_STORAGE_URL}/{generate_blob_name_uuid(flag.kind)}'"
                        )
                        continue

                    blob_schema = None
                    error_message = None

                    if is_blob_storage_url(old_url):
                        # Copy from old blob storage
                        try:
                            blob_schema = copy_blob(
                                old_url,
                                flag.flag_name,
                                flag.kind,
                            )
                            blobs_to_delete.add(old_url)
                        except Exception as exc:
                            error_message = f"Copy failed: {exc!s}"
                    else:
                        # Download from external URL and upload to blob storage
                        try:
                            blob_schema = upload_blob(
                                old_url,
                                flag.flag_name,
                                flag.kind,
                            )
                        except Exception as exc:
                            error_message = f"Download/upload failed: {exc!s}"

                    if blob_schema:
                        create_or_update_blob(
                            session, schedule_id=schedule.id, request=blob_schema
                        )
                        setattr(
                            schedule_config.offliner,
                            flag.flag_name,
                            str(blob_schema.url),
                        )
                        schedule.config = schedule_config.model_dump(
                            mode="json", context={"show_secrets": True}
                        )
                        total_assets_migrated += 1
                        logger.info(
                            f"✅ Migrated schedule '{schedule.name}' flag "
                            f"'{flag.flag_name}' to '{blob_schema.url!s}'"
                        )
                    else:
                        unavailable_assets.append(
                            UnavailableAsset(
                                schedule=schedule.name,
                                flag=flag.flag_name,
                                url=old_url,
                                error=error_message or "Unknown error",
                            )
                        )
                        logger.error(
                            f"❌ Could not migrate schedule '{schedule.name}' flag "
                            f"'{flag.flag_name}': {error_message}"
                        )

    # Delete old blobs from storage
    logger.info(f"Deleting {len(blobs_to_delete)} old blobs from storage...")
    for blob_url in blobs_to_delete:
        delete_blob(blob_url)

    # Generate and display markdown report
    print("\n" + "=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Total assets migrated: {total_assets_migrated}")
    print(f"Total assets skipped (already migrated): {total_assets_skipped}")
    print(f"Total assets filtered (excluded by rules): {total_assets_filtered}")
    print(f"Total assets unavailable: {len(unavailable_assets)}")
    print("=" * 80)

    markdown_report = generate_markdown_report(unavailable_assets)
    print("\n" + markdown_report)

    print("\n" + "=" * 80)
    print("FINISH!")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Update schedule flags thats are blob URLs by moving them to "
            "unified storage."
        ),
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Do not apply the changes"
    )

    parser.add_argument(
        "--filter",
        action="append",
        dest="filters",
        metavar="SCHEDULE_PATTERN:FLAG_NAME",
        help=(
            "Filter out URLs from migration using format "
            "'schedule_pattern:flag_name'. Use '.*' as wildcard. Can be used "
            "multiple times. Examples: --filter 'test.*:favicon' "
            "--filter '.*:banner'"
        ),
    )

    args = parser.parse_args()

    filter_rules: list[FilterRule] = []

    if args.filters:
        for filter_str in args.filters:
            if ":" not in filter_str:
                raise ValueError(
                    f"Warning: Invalid filter format '{filter_str}', "
                    "expected 'schedule_pattern:flag_name'"
                )
            schedule_pattern, flag_name = filter_str.split(":", 1)
            filter_rules.append(
                FilterRule(schedule_pattern=schedule_pattern, flag_name=flag_name)
            )

    main(dry_run=args.dry_run, filter_rules=filter_rules)
