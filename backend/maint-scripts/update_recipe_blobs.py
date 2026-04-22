#!/usr/bin/env python3

# ruff: noqa: T201

import argparse
import hashlib
import re
from typing import Literal

import requests
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common.constants import (
    API_ENDPOINT,
    REQUESTS_TIMEOUT,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import RecipeConfigSchema
from zimfarm_backend.common.schemas.orms import CreateBlobSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.blob import create_blob_schema, create_or_update_blob, get_blob
from zimfarm_backend.db.models import Blob, Recipe
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
)


class BlobFlag(BaseModel):
    flag_name: str
    kind: Literal["image", "css", "html", "txt"]


class UnavailableAsset(BaseModel):
    recipe: str
    flag: str
    url: str
    error: str


class FilterRule(BaseModel):
    """Filter rule to exclude certain recipe/flag combinations from migration"""

    recipe_pattern: str
    flag_name: str

    def matches(self, recipe_name: str, flag_name: str) -> bool:
        """Check if this rule matches the given recipe and flag"""
        recipe_match = bool(re.search(self.recipe_pattern, recipe_name))
        flag_match = flag_name == self.flag_name
        return recipe_match and flag_match


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


def download_blob(url: str, flag_name: str, kind: str) -> CreateBlobSchema | None:
    """
    Download blob from external url and compute blob checksum
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

    return CreateBlobSchema(
        flag_name=flag_name,
        kind=kind,
        checksum=checksum,
        comments=f"Original URL: {url}",
        content=blob_data,
    )


def is_blob_storage_url(url: str) -> bool:
    """Check if URL is blob storage (same domain but different path)"""
    return url.startswith(API_ENDPOINT.rsplit("/", 1)[0])


def generate_markdown_report(unavailable_assets: list[UnavailableAsset]) -> str:
    """Generate a markdown report of unavailable assets ready for GitHub issue"""
    if not unavailable_assets:
        return "## Migration Report\n\nAll assets migrated successfully!"

    report_lines = [
        "## Unavailable Assets Report",
        "",
        "The following assets could not be migrated and require manual fixing:",
        "",
        "| Recipe | Flag | URL | Error |",
        "|----------|------|-----|-------|",
    ]

    for asset in unavailable_assets:
        # Escape pipe characters in fields for markdown table
        recipe = asset.recipe.replace("|", "\\|")
        flag = asset.flag.replace("|", "\\|")
        url = asset.url.replace("|", "\\|")
        error = asset.error.replace("|", "\\|")
        report_lines.append(f"| {recipe} | {flag} | {url} | {error} |")

    report_lines.extend(
        ["", f"**Total unavailable assets:** {len(unavailable_assets)}"]
    )

    return "\n".join(report_lines)


def main(*, dry_run: bool = False, filter_rules: list[FilterRule] | None = None):
    # list of blob urls to delete after copying them to new locations
    unavailable_assets: list[UnavailableAsset] = []
    total_assets_migrated = 0
    total_assets_skipped = 0
    total_assets_filtered = 0

    if filter_rules is None:
        filter_rules = []

    def should_filter(recipe_name: str, flag_name: str) -> bool:
        """Check if recipe/flag combination should be filtered out"""
        return any(rule.matches(recipe_name, flag_name) for rule in filter_rules)

    for offliner_id, flag_mappings in FLAG_MAPPINGS.items():
        logger.info(f"Processing offliner: {offliner_id}")

        with Session() as session:
            offliner = get_offliner(session, offliner_id)

            recipes = session.execute(
                select(Recipe)
                .where(
                    Recipe.config["offliner"]["offliner_id"].astext == offliner_id,
                )
                .options(selectinload(Recipe.offliner_definition))
            ).scalars()

            for recipe in recipes:
                logger.info(f"Processing recipe {recipe.name}...")
                offliner_definition = create_offliner_definition_schema(
                    recipe.offliner_definition
                )
                recipe_config = RecipeConfigSchema.model_validate(
                    {
                        **recipe.config,
                        "offliner": create_offliner_instance(
                            offliner=offliner,
                            offliner_definition=offliner_definition,
                            data=recipe.config["offliner"],
                            skip_validation=True,
                        ),
                    },
                    context={"skip_validation": True},
                )

                for flag in flag_mappings:
                    flag_url = getattr(recipe_config.offliner, flag.flag_name)
                    if not flag_url:
                        logger.info(
                            f"{recipe.name} flag '{flag.flag_name}' has no URL."
                        )
                        continue

                    if not flag_url.startswith("http"):
                        logger.warning(
                            f"Recipe '{recipe.name}' flag "
                            f"'{flag.flag_name}' is not a valid URL, skipping"
                        )
                        continue

                    # Check if this recipe/flag combination should be filtered
                    if should_filter(recipe.name, flag.flag_name):
                        logger.info(
                            f"🚫 Filtered recipe '{recipe.name}' flag "
                            f"'{flag.flag_name}' (matches filter rule)"
                        )
                        total_assets_filtered += 1
                        continue

                    # Check if there is a blob with content whose URL matches the
                    # same one as the flag value
                    existing_blobs = session.scalars(
                        select(Blob).where(
                            Blob.flag_name == flag.flag_name,
                            Blob.recipe_id == recipe.id,
                            Blob.content.is_not(None),
                        )
                    ).all()

                    if existing_blobs:
                        should_skip = False
                        for existing_blob in existing_blobs:
                            existing_blob_schema = create_blob_schema(existing_blob)
                            if flag_url == existing_blob_schema.url:
                                should_skip = True
                                break

                        if should_skip:
                            logger.info(
                                f"Recipe '{recipe.name}' flag '{flag.flag_name}' "
                                "already has blob entry, skipping"
                            )
                            total_assets_skipped += 1
                            continue

                    if dry_run:
                        total_assets_migrated += 1
                        logger.info(
                            f"✅ Migrated recipe '{recipe.name}' flag "
                            f"'{flag.flag_name}' to "
                            f"'{API_ENDPOINT}"
                        )
                        continue

                    blob_schema = None
                    error_message = None

                    # Download from external URL and upload to blob storage
                    try:
                        blob_schema = download_blob(
                            flag_url,
                            flag.flag_name,
                            flag.kind,
                        )
                    except Exception as exc:
                        error_message = (
                            f"Download failed with following reason: {exc!s}"
                        )

                    if blob_schema:
                        create_or_update_blob(
                            session, recipe_id=recipe.id, request=blob_schema
                        )
                        new_blob = get_blob(
                            session,
                            recipe_id=recipe.id,
                            flag_name=flag.flag_name,
                            checksum=blob_schema.checksum,
                        )
                        setattr(
                            recipe_config.offliner,
                            flag.flag_name,
                            str(new_blob.url),
                        )
                        recipe.config = recipe_config.model_dump(
                            mode="json", context={"show_secrets": True}
                        )
                        session.add(recipe)
                        session.commit()
                        total_assets_migrated += 1
                        logger.info(
                            f"✅ Migrated recipe '{recipe.name}' flag "
                            f"'{flag.flag_name}' to '{new_blob.url!s}'"
                        )
                    else:
                        unavailable_assets.append(
                            UnavailableAsset(
                                recipe=recipe.name,
                                flag=flag.flag_name,
                                url=flag_url,
                                error=error_message or "Unknown error",
                            )
                        )
                        logger.error(
                            f"❌ Could not migrate recipe '{recipe.name}' flag "
                            f"'{flag.flag_name}': {error_message}"
                        )

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
            "Update recipe flags thats are blob URLs by moving them to unified storage."
        ),
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Do not apply the changes"
    )

    parser.add_argument(
        "--filter",
        action="append",
        dest="filters",
        metavar="RECIPE_PATTERN:FLAG_NAME",
        help=(
            "Filter out URLs from migration using format "
            "'recipe_pattern:flag_name'. Use '.*' as wildcard. Can be used "
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
                    "expected 'recipe_pattern:flag_name'"
                )
            recipe_pattern, flag_name = filter_str.split(":", 1)
            filter_rules.append(
                FilterRule(recipe_pattern=recipe_pattern, flag_name=flag_name)
            )

    main(dry_run=args.dry_run, filter_rules=filter_rules)
