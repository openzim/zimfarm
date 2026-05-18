#!/usr/bin/env python3

"""
Create default recipe durations for recipes that do not have a default duration

./create_default_recipe_durations
"""

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Recipe, RecipeDuration
from zimfarm_backend.db.recipe import DEFAULT_RECIPE_DURATION


def create_default_recipe_durations(session: OrmSession):
    logger.info("Looking for recipes without a default duration")

    stmt = sa.select(Recipe.id, Recipe.name).where(
        Recipe.id.not_in(
            sa.select(sa.distinct(RecipeDuration.recipe_id)).where(
                RecipeDuration.default.is_(True)
            )
        )
    )

    nb_created = 0
    for recipe_id, recipe_name in session.execute(stmt).all():
        duration = RecipeDuration(
            default=True,
            value=DEFAULT_RECIPE_DURATION.value,
            on=DEFAULT_RECIPE_DURATION.on,
        )
        duration.recipe_id = recipe_id
        session.add(duration)

        logger.info(f"Created default duration for {recipe_name}")
        nb_created += 1

    logger.info(f"Created {nb_created} recipe duration(s)")


if __name__ == "__main__":
    with Session.begin() as session:
        create_default_recipe_durations(session=session)
    logger.info("FINISH!")
