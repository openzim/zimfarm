#!/usr/bin/env python3
import argparse
from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common.constants import API_ENDPOINT
from zimfarm_backend.common.schemas.models import RecipeConfigSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.account import get_account_by_username
from zimfarm_backend.db.models import Recipe, RecipeHistory
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
)
from zimfarm_backend.db.recipe import update_recipe


def main(*, dry_run: bool = False):
    with Session() as session:
        user = get_account_by_username(session, username="maint-scripts")
        offliner_id = "mwoffliner"
        offliner = get_offliner(session, offliner_id)

        recipes = (
            session.execute(
                select(Recipe)
                .where(Recipe.config["offliner"]["offliner_id"].astext == offliner_id)
                .options(selectinload(Recipe.offliner_definition))
            )
            .scalars()
            .all()
        )

        for recipe in recipes:
            article_list = recipe.config.get("offliner", {}).get("articleList")
            if not article_list:
                logger.info(
                    f"Recipe '{recipe.name}' does not have an articleList set. "
                    "Skipping..."
                )
                continue

            if not (
                article_list.startswith(API_ENDPOINT)
                or article_list.startswith("https://farm.drive.openzim.org")
            ):
                logger.info(
                    f"Recipe '{recipe.name} articleList already set to external URL: "
                    f"'{article_list}'. Skipping..."
                )
                continue

            histories = (
                session.execute(
                    select(RecipeHistory)
                    .where(RecipeHistory.recipe_id == recipe.id)
                    .order_by(RecipeHistory.created_at.desc())
                )
                .scalars()
                .all()
            )

            found_old_url = None
            for history in histories:
                hist_article_list = history.config.get("offliner", {}).get(
                    "articleList"
                )
                if hist_article_list and not (
                    hist_article_list.startswith(API_ENDPOINT)
                    or hist_article_list.startswith("https://farm.drive.openzim.org")
                ):
                    found_old_url = hist_article_list
                    break

            if found_old_url:
                logger.info(f"Found old articleList for {recipe.name}: {found_old_url}")
                if dry_run:
                    logger.info(
                        f"[dry run]: Changed articleList for {recipe.name} from "
                        f"{article_list} to {found_old_url}."
                    )
                    continue

                offliner_def = create_offliner_definition_schema(
                    recipe.offliner_definition
                )
                new_config = deepcopy(recipe.config)
                new_config["offliner"]["articleList"] = found_old_url

                recipe_config = RecipeConfigSchema.model_validate(
                    {
                        **new_config,
                        "offliner": create_offliner_instance(
                            offliner=offliner,
                            offliner_definition=offliner_def,
                            data=new_config["offliner"],
                            skip_validation=True,
                        ),
                    },
                    context={"skip_validation": True},
                )

                update_recipe(
                    session=session,
                    author_id=user.id,
                    recipe_name=recipe.name,
                    offliner_definition=offliner_def,
                    new_recipe_config=recipe_config,
                    comment="Restore mwoffliner articleList from history",
                )
                session.commit()
                logger.info(
                    f"Changed articleList for {recipe.name} from "
                    f"{article_list} to {found_old_url}."
                )
            else:
                logger.warning(f"Could not find old articleList for {recipe.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Restore mwoffliner articleList from history"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not apply the changes"
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
