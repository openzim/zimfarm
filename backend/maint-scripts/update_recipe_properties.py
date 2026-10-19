#!/usr/bin/env python3

"""
Update scalar properties of recipes matching a set of filters.

EXAMPLES:

1. Set the periodicity of all quarterly mwoffliner recipes to monthly:
   ./update_recipe_properties.py \
       --filters="periodicity=quarterly|offliner=mwoffliner" \
       --values="periodicity=monthly"

2. Disable all recipes for the youtube offliner:
   ./update_recipe_properties.py \
       --filters="offliner=youtube" \
       --values="enabled=false"

3. Set the platform of all sotoki recipes to stackexchange:
   ./update_recipe_properties.py \
       --filters="offliner=sotoki" \
       --values="platform=stackexchange"

4. Move all ted recipes to the ted warehouse path and enable monitoring:
   ./update_recipe_properties.py \
       --filters="offliner=ted" \
       --values="warehouse_path=/ted|monitor=true"

5. Remove the platform of all recipes of the youtube platform:
   ./update_recipe_properties.py \
       --filters="platform=youtube" \
       --values="platform="

6. Preview the changes without applying them:
   ./update_recipe_properties.py \
       --filters="offliner=zimit" \
       --values="periodicity=monthly" \
       --dry-run

Supported filter attributes:
    name, offliner, platform, warehouse_path (empty value matches the root
    path), monitor, language, periodicity, context, tags, teams, enabled,
    is_valid, archived

Supported value attributes (scalar attributes, plus lists via
comma-separated values):
    name, language, periodicity, context, tags, teams, enabled, is_valid,
    platform (empty value removes the platform), warehouse_path, monitor,
    artifacts_globs
"""

import argparse
import sys
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common.constants import parse_bool
from zimfarm_backend.common.enums import Platform, RecipePeriodicity, WarehousePath
from zimfarm_backend.common.schemas.models import RecipeConfigSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.account import get_account_by_username
from zimfarm_backend.db.language import get_language_from_code
from zimfarm_backend.db.models import Recipe, Team, TeamRecipe
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
)
from zimfarm_backend.db.recipe import RecipeUpdateSchema, update_recipe


def split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# Mapping of supported filter attributes to a callable building the SQL clause
FILTER_ATTRIBUTES: dict[str, Callable[[str], Any]] = {
    "name": lambda value: Recipe.name.in_(split_list(value)),
    "offliner": lambda value: Recipe.config["offliner"]["offliner_id"].astext.in_(
        split_list(value)
    ),
    "platform": lambda value: Recipe.config["platform"].astext.in_(split_list(value)),
    # empty items are kept since the root warehouse path is an empty string
    "warehouse_path": lambda value: Recipe.config["warehouse_path"].astext.in_(
        [item.strip() for item in value.split(",")]
    ),
    "monitor": lambda value: (
        Recipe.config["monitor"].as_boolean().is_(parse_bool(value))
    ),
    "language": lambda value: Recipe.language_code.in_(split_list(value)),
    "periodicity": lambda value: Recipe.periodicity.in_(split_list(value)),
    "context": lambda value: Recipe.context.in_(split_list(value)),
    "tags": lambda value: Recipe.tags.contains(split_list(value)),
    "teams": lambda value: Recipe.teams.any(
        TeamRecipe.team.has(Team.name.in_(split_list(value)))
    ),
    "enabled": lambda value: Recipe.enabled.is_(parse_bool(value)),
    "is_valid": lambda value: Recipe.is_valid.is_(parse_bool(value)),
    "archived": lambda value: Recipe.archived.is_(parse_bool(value)),
}

# Mapping of supported value attributes to a callable converting the raw string
# into the value accepted by RecipeUpdateSchema.
UPDATABLE_ATTRIBUTES: dict[str, Callable[[str], Any]] = {
    "name": lambda value: value,
    "periodicity": RecipePeriodicity,
    "context": lambda value: value,
    "tags": split_list,
    "teams": split_list,
    "enabled": parse_bool,
    "is_valid": parse_bool,
}

# Mapping of supported value attributes stored in the recipe config to a callable
# converting the raw string into the value accepted by RecipeConfigSchema.
UPDATABLE_CONFIG_ATTRIBUTES: dict[str, Callable[[str], Any]] = {
    "platform": lambda value: Platform(value) if value else None,
    "warehouse_path": WarehousePath,
    "monitor": parse_bool,
    "artifacts_globs": split_list,
}


def parse_pairs(raw: str) -> dict[str, str]:
    """Parse a pipe-separated list of attribute=value pairs."""
    pairs: dict[str, str] = {}
    for raw_item in raw.split("|"):
        item = raw_item.strip()
        if not item:
            continue
        key, separator, value = item.partition("=")
        if not separator:
            raise ValueError(
                f"Invalid pair '{item}': expected format 'attribute=value'"
            )
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid pair '{item}': empty attribute name")
        pairs[key] = value.strip()
    return pairs


def build_filters(pairs: dict[str, str]) -> list[Any]:
    """Build the list of SQL clauses from the parsed filter pairs."""
    clauses: list[Any] = []
    for key, value in pairs.items():
        if key not in FILTER_ATTRIBUTES:
            raise ValueError(
                f"Unknown filter attribute '{key}'. Supported attributes: "
                f"{', '.join(sorted(FILTER_ATTRIBUTES))}"
            )
        clauses.append(FILTER_ATTRIBUTES[key](value))
    return clauses


def build_updates(pairs: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the recipe and recipe config update values from the parsed pairs."""
    updates: dict[str, Any] = {}
    config_updates: dict[str, Any] = {}
    for key, value in pairs.items():
        if key == "language":
            updates[key] = get_language_from_code(value)
        elif key in UPDATABLE_ATTRIBUTES:
            updates[key] = UPDATABLE_ATTRIBUTES[key](value)
        elif key in UPDATABLE_CONFIG_ATTRIBUTES:
            config_updates[key] = UPDATABLE_CONFIG_ATTRIBUTES[key](value)
        else:
            supported = [
                *UPDATABLE_ATTRIBUTES,
                *UPDATABLE_CONFIG_ATTRIBUTES,
                "language",
            ]
            raise ValueError(
                f"Unknown value attribute '{key}'. Supported attributes: "
                f"{', '.join(sorted(supported))}"
            )
    return updates, config_updates


def build_config(
    session: OrmSession, recipe: Recipe, config_updates: dict[str, Any]
) -> RecipeConfigSchema:
    """Build the recipe config with the config updates applied"""
    return RecipeConfigSchema.model_validate(
        {
            **recipe.config,
            **config_updates,
            "offliner": create_offliner_instance(
                offliner=get_offliner(
                    session, recipe.config["offliner"]["offliner_id"]
                ),
                offliner_definition=recipe.offliner_definition,
                data=recipe.config["offliner"],
                skip_validation=True,
            ),
        },
        context={"skip_validation": True},
    )


def main(
    *,
    filters: dict[str, str],
    values: dict[str, str],
    comment: str | None,
    dry_run: bool,
    username: str,
) -> None:
    filter_clauses = build_filters(filters)
    updates, config_updates = build_updates(values)

    with Session() as session:
        stmt = (
            select(Recipe)
            .options(selectinload(Recipe.offliner_definition))
            .order_by(Recipe.name)
        )
        for clause in filter_clauses:
            stmt = stmt.where(clause)

        recipes = session.scalars(stmt).all()
        author_id = get_account_by_username(session, username=username).id

        logger.info(f"Matched {len(recipes)} recipe(s)")

        nb_updated = 0
        for recipe in recipes:
            if recipe.archived:
                logger.warning(f"Recipe '{recipe.name}' is archived. Skipping.")
                continue

            if dry_run:
                logger.info(f"[dry-run] Would update recipe '{recipe.name}'")
                nb_updated += 1
                continue

            update_recipe(
                session,
                author_id=author_id,
                recipe_identifier=recipe.name,
                accessible_team_ids=None,
                payload=RecipeUpdateSchema(
                    offliner_definition=create_offliner_definition_schema(
                        recipe.offliner_definition
                    ),
                    config=(
                        build_config(session, recipe, config_updates)
                        if config_updates
                        else None
                    ),
                    comment=comment,
                    **updates,
                ),
            )
            session.commit()
            nb_updated += 1
            logger.info(f"Updated recipe '{recipe.name}'")

        if dry_run:
            logger.info(f"[dry-run] Would have updated {nb_updated} recipe(s)")
        else:
            logger.info(f"Updated {nb_updated} recipe(s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Update scalar properties of recipes matching a set of filters. "
            "Both filters and values are pipe-separated lists of "
            "'attribute=value' pairs."
        ),
    )

    parser.add_argument(
        "--filters",
        default="",
        help=(
            "Pipe-separated list of 'attribute=value' filters used to select "
            "recipes, e.g. 'periodicity=quarterly|offliner=mwoffliner'. When "
            "omitted, every (non-archived) recipe is targeted."
        ),
    )

    parser.add_argument(
        "--values",
        required=True,
        help=(
            "Pipe-separated list of 'attribute=value' pairs to set on the "
            "matched recipes, e.g. 'periodicity=monthly'. List attributes "
            "(tags, teams, artifacts_globs) accept comma-separated values. An "
            "empty platform value removes the platform."
        ),
    )

    parser.add_argument(
        "--comment",
        default="Updated via update_recipe_properties",
        help="Comment recorded in the recipe history entry for each update.",
    )

    parser.add_argument(
        "--username", required=True, help="Username of account applying these updates."
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Do not apply the changes"
    )

    args = parser.parse_args()

    try:
        filters = parse_pairs(args.filters)
        values = parse_pairs(args.values)
        if not filters:
            logger.warning("No filters provided: targeting all non-archived recipes.")
        if not values:
            raise ValueError("No values provided: nothing to update.")
        main(
            filters=filters,
            values=values,
            comment=args.comment,
            dry_run=args.dry_run,
            username=args.username,
        )
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    logger.info("FINISH!")
