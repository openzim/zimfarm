#!/usr/bin/env python3

"""
Add recipe category to its tags. Only the following categories are added to tags:
vikidia, wikibooks, wikinews, wikipedia, wikiquoute, wikisource, wikispecies,
wikiversity, wikivoyage, wiktionary

"""

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Recipe
from zimfarm_backend.db.recipe import get_recipe


def add_category_to_tags(recipe: Recipe):
    if recipe.category in recipe.tags:
        logger.info(
            f"Skipped {recipe.name} as category {recipe.category} already exists in "
            "tags"
        )
        return

    recipe.tags.append(recipe.category)
    flag_modified(recipe, "tags")
    logger.info(f"Added {recipe.category} to {recipe.name} tags.")


if __name__ == "__main__":
    with Session.begin() as session:
        recipe_names = session.scalars(
            select(Recipe.name).where(
                Recipe.category.in_(
                    [
                        "vikidia",
                        "wikibooks",
                        "wikinews",
                        "wikipedia",
                        "wikiquote",
                        "wikisource",
                        "wikispecies",
                        "wikiversity",
                        "wikivoyage",
                        "wiktionary",
                    ]
                )
            )
        ).all()
        for recipe_name in recipe_names:
            recipe = get_recipe(session, recipe_name)
            add_category_to_tags(recipe)
    logger.info("FINISH!")
