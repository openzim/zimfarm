#!/usr/bin/env python3
"""
Import Recipes Script

This script helps you import a backup of recipes defined in the production system.

Usage:
    1. First, download the backup from production:
       curl https://api.farm.openzim.org/v1/recipes/backup/ > /tmp/all_recipes.json

    2. Set the POSTGRES_URI and ZIMFARM_USERNAME environment variables:
       export POSTGRES_URI=postgresql+psycopg://zimfarm:zimpass@localhost:5432/zimfarm
       export ZIMFARM_USERNAME=admin

    3. Run this script:
       python import_recipes.py /tmp/all_recipes.json

"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.user import get_user_by_username
from zimfarm_backend.common.schemas.orms import RecipeConfigSchema
from zimfarm_backend.db.offliner_definition import (
    create_offliner_instance,
    get_offliner_definition_or_none,
)
from zimfarm_backend.common.enums import RecipeCategory, RecipePeriodicity
from zimfarm_backend.db.recipe import create_recipe
from zimfarm_backend.common.constants import getenv
from zimfarm_backend.common.schemas.models import RecipeNotificationSchema
from zimfarm_backend.db.language import get_language_from_code
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.models import User


def import_recipes(
    session: OrmSession, backup_data: list[dict[str, Any]], user: User
) -> None:
    successful = failed = 0
    for data in backup_data:
        offliner_definition = get_offliner_definition_or_none(
            session, offliner_id=data["offliner"], version="dev"
        )
        if offliner_definition is None:
            logger.warning(
                f"Offliner definition for offliner {data['offliner']} with "
                "with version 'dev' does not exist. Skipping creation of "
                f"{data['name']}"
            )
            failed = 0
            continue

        config = RecipeConfigSchema.model_validate(
            {
                **data["config"],
                "offliner": create_offliner_instance(
                    offliner=get_offliner(session, offliner_definition.offliner),
                    offliner_definition=offliner_definition,
                    data=data["config"]["offliner"],
                    skip_validation=True,
                    extra="ignore",
                ),
            }
        )

        create_recipe(
            session,
            author_id=user.id,
            language=get_language_from_code(data["language"]["code"]),
            name=data["name"],
            offliner_definition=offliner_definition,
            category=RecipeCategory(data["category"]),
            config=config,
            tags=data["tags"],
            enabled=data["enabled"],
            notification=(
                RecipeNotificationSchema.model_validate(data["notification"])
                if data.get("notification")
                else None
            ),
            periodicity=RecipePeriodicity(data["periodicity"]),
            context=data["context"] if data["context"] else None,
        )
        logger.info(f"✓ Created recipe: {data['name']}")
        successful += 1

    logger.info(f"Imported recipes, {successful=}, {failed=}")


def main():
    parser = argparse.ArgumentParser(
        description="Import recipes from a backup JSON file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "backup_file",
        type=Path,
        help="Path to the backup JSON file (e.g., /tmp/all_recipes.json)",
    )
    args = parser.parse_args()

    getenv("POSTGRES_URI", mandatory=True)
    username = getenv("INIT_USERNAME", mandatory=True)

    if not args.backup_file.exists():
        print(f"Error: Backup file not found: {args.backup_file}")
        sys.exit(1)

    logger.info(f"Reading backup file: {args.backup_file}")
    with open(args.backup_file, "r") as f:
        backup_data = json.load(f)

    if not isinstance(backup_data, list):
        logger.error("Backup file must contain a JSON array of recipes")
        sys.exit(1)

    logger.info(f"Found {len(backup_data)} recipes in backup file")

    with Session.begin() as session:
        user = get_user_by_username(session, username=username)
        import_recipes(session=session, backup_data=backup_data, user=user)


if __name__ == "__main__":
    main()
