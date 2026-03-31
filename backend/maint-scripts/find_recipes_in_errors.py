#!/usr/bin/env python3

"""Find all recipes which are enabled and have at least the last two tasks which
failed in a row

./find_recipes_in_errors"""

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Recipe


def find_recipes_in_errors(session: OrmSession):
    logger.info("Looking after recipes with bad status")

    stmt = sa.select(Recipe).where(Recipe.enabled).order_by(Recipe.name)

    recipes = list(session.execute(stmt).scalars())
    logger.info(f"{len(recipes)} recipes found")

    for recipe in recipes:
        all_tasks = sorted(recipe.tasks, key=lambda t: t.updated_at, reverse=True)

        nb_failed = len(list(filter(lambda t: t.status == "failed", all_tasks)))
        nb_success = len(list(filter(lambda t: t.status == "succeeded", all_tasks)))
        total = len(all_tasks)

        if nb_success == 0:
            logger.info(
                f"Never succeeded: recipe {recipe.name} (periodicity="
                f"{recipe.periodicity}) never succeeded out of {total} attempts"
            )
            continue

        if nb_failed > 1:
            nb_failures_in_a_row = 0
            for task in all_tasks:
                if task.status != "failed":
                    break
                nb_failures_in_a_row += 1

            if nb_failures_in_a_row > 1:
                logger.info(
                    f"Many failures in a row: recipe {recipe.name} (periodicity="
                    f"{recipe.periodicity}) failed {nb_failures_in_a_row} times in"
                    f" a row, nb_success: {nb_success}, nb_failed: {nb_failed},"
                    f" total: {total}"
                )
                continue


if __name__ == "__main__":
    with Session.begin() as session:
        find_recipes_in_errors(session=session)
    logger.info("FINISH!")
