#!/usr/bin/env python3

"""This script scans through all the blobs in the database that do not have their
content stored in the DB, fetches them from their URL and stores the content to
the database.

It logs the names of recipes for which we failed to fetch their content from the URL.

Script should be deleted once the URL property of the Blob has been removed and
content made non-nullable.
"""

from uuid import UUID

import requests
from sqlalchemy import select

from zimfarm_backend import logger
from zimfarm_backend.common.constants import REQUESTS_TIMEOUT
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Blob, Recipe


def main():
    with Session() as session:
        stmt = select(Blob).where(Blob.content.is_(None))
        blobs = session.scalars(stmt).all()

        if not blobs:
            logger.info("No blobs without content found.")
            return

        logger.info(f"Found {len(blobs)} blobs to process.")
        nb_success = 0
        nb_failed = 0
        # List of recipes for which we failed to fetch their blobs
        failed_recipe_ids: list[UUID] = []

        for blob in blobs:
            logger.info(f"Fetching content for blob ID {blob.id} from {blob.url}...")
            if not blob.url:
                logger.error(f"Blob {blob.id} has no URL to fetch content.")
                nb_failed += 1
                if blob.recipe_id:
                    failed_recipe_ids.append(blob.recipe_id)
                continue
            try:
                response = requests.get(blob.url, timeout=REQUESTS_TIMEOUT)
                response.raise_for_status()

                blob.content = response.content
                session.add(blob)
                session.commit()
                nb_success += 1
                logger.info(f"Successfully updated blob ID {blob.id}.")
            except Exception as e:
                logger.error(f"An unexpected error occurred for blob ID {blob.id}: {e}")
                nb_failed += 1
                if blob.recipe_id:
                    failed_recipe_ids.append(blob.recipe_id)

        logger.info(f"Saved blob contents to database, {nb_success=}, {nb_failed=}")

        if failed_recipe_ids:
            recipe_names = list(
                session.scalars(
                    select(Recipe.name).where(Recipe.id.in_(failed_recipe_ids))
                ).all()
            )
            logger.info(
                "Failed to fetch blobs for the following recipes: \n"
                f"{'\n'.join(recipe_names)}"
            )


if __name__ == "__main__":
    main()
