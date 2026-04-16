#!/usr/bin/env python3

"""
Script to validate all recipes and generate a markdown report of validation errors.

EXAMPLES:

1. Validate all recipes and generate a report:
   ./validate_all_recipes.py

2. Validate all recipes including archived ones:
   ./validate_all_recipes.py --include-archived

"""

import argparse
from collections import defaultdict
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Recipe
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.recipe import create_recipe_full_schema


def transform_validation_errors(exc: ValidationError) -> dict[str | int, list[str]]:
    errors: dict[str | int, list[str]] = defaultdict(list)
    for err in exc.errors():
        loc = err["loc"]
        key = loc[-1] if loc else "root"  # fallback for model level errors
        errors[key].append(err["msg"])
    return errors


def validate_recipes(
    session: OrmSession, *, include_archived: bool = False
) -> list[dict[str, Any]]:
    """Validate all recipes and return a list of recipes with validation errors"""
    results: list[dict[str, Any]] = []

    for recipe in session.scalars(
        select(Recipe).where(Recipe.archived == include_archived).order_by(Recipe.name)
    ).all():
        logger.info(f"Validating recipe: {recipe.name}")

        try:
            offliner = get_offliner(session, recipe.config["offliner"]["offliner_id"])
            create_recipe_full_schema(recipe, offliner, skip_validation=False)
            logger.info(f"  ✓ Recipe '{recipe.name}' is valid")
        except ValidationError as exc:
            errors = transform_validation_errors(exc)
            results.append(
                {"name": recipe.name, "errors": errors, "archived": recipe.archived}
            )
            logger.warning(f"  ✗ Recipe '{recipe.name}' has validation errors")
        except Exception as exc:
            logger.exception(
                f"  ✗ Unexpected error validating recipe '{recipe.name}': {exc}"
            )
            results.append(
                {
                    "name": recipe.name,
                    "errors": {"root": [f"Unexpected error: {exc!s}"]},
                    "archived": recipe.archived,
                }
            )

    return results


def generate_markdown_report(results: list[dict[str, Any]]) -> str:
    """Generate a markdown report from validation results"""
    if not results:
        return "# Recipe Validation Report\n\n✅ All recipes are valid!\n"

    report = "# Recipe Validation Report\n\n"
    report += f"Found **{len(results)}** recipe(s) with validation errors.\n\n"
    report += "| Recipe | Errors |\n"
    report += "|--------|--------|\n"

    for result in results:
        recipe_name = result["name"]
        errors = result["errors"]
        archived_status = " (ARCHIVED)" if result["archived"] else ""

        error_items: list[str] = []
        for field, error_list in errors.items():
            for error_msg in error_list:
                error_items.append(f"- **{field}**: {error_msg}")

        errors_cell = "<br>".join(error_items)

        report += f"| {recipe_name}{archived_status} | {errors_cell} |\n"

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate all recipes and generate a markdown report of errors",
    )

    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived recipes in validation",
    )

    args = parser.parse_args()

    with Session.begin() as session:
        results = validate_recipes(session, include_archived=args.include_archived)

    report = generate_markdown_report(results)
    print(report)  # noqa: T201

    if results:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Validation complete: {len(results)} recipe(s) with errors")
        logger.info(f"{'=' * 60}")
    else:
        logger.info(f"\n{'=' * 60}")
        logger.info("Validation complete: All recipes are valid!")
        logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
