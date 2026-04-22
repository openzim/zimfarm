#!/usr/bin/env python3

"""
Script to update similarity data of offliner definitions and recipes

EXAMPLES:

1. Update the similarity data for all offliner definitions. This updates the recipes
   similarity data too. Input can be a JSON file or sent via stdin.
   ./update_similarity_data.py -o mwoffliner -s simialrity_data.in

2 To update via stdin:
   echo '[
      {
        "flag": "mwUrl",
        "transformers": [
          {
            "name": "hostname",
            "operand": null
          }
        ]
      }
    ]' \
    | ./update_similarity_data.py \
      -o mwoffliner \
      -s
"""

import argparse
import json
import sys

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend import logger
from zimfarm_backend.common.schemas.offliners.builder import generate_similarity_data
from zimfarm_backend.common.schemas.offliners.models import (
    OfflinerSpecSchema,
    SimilarityDataSchema,
)
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import OfflinerDefinition, Recipe
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
)
from zimfarm_backend.db.recipe import create_recipe_full_schema


def update_recipes(
    session: OrmSession,
    *,
    offliner: OfflinerSchema,
    offliner_definition: OfflinerDefinitionSchema,
) -> int:
    nb_modified: int = 0

    for recipe in session.execute(
        sa.select(Recipe).where(
            Recipe.config["offliner"]["offliner_id"].astext == offliner.id,
            Recipe.offliner_definition_id == offliner_definition.id,
        )
    ).scalars():
        logger.info(f"setting similarity data for recipe {recipe.name}")
        recipe.similarity_data = generate_similarity_data(
            recipe.config["offliner"], offliner, offliner_definition.schema_
        )
        flag_modified(recipe, "config")
        create_recipe_full_schema(recipe, offliner)
        nb_modified += 1
    return nb_modified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update recipes and requested tasks image tag "
        "or offliner definition",
    )

    # Required offliner specification
    parser.add_argument(
        "-o", "--offliner", required=True, help="Specify which offliner to update"
    )

    parser.add_argument(
        "-s",
        "--similarity-data",
        metavar="SIMILARITY DATA",
        type=argparse.FileType("r", encoding="utf-8"),
        const=sys.stdin,
        nargs="?",
        help=(
            "List of similarity data transformers to apply to all definitions of the "
            "offliner. This updates the similarity data array of the recipes "
            "associated with the definitions too."
        ),
    )

    args = parser.parse_args()

    with Session.begin() as session:
        offliner = get_offliner(session, args.offliner)

        if args.similarity_data:
            similarity_data = [
                SimilarityDataSchema.model_validate(data)
                for data in json.loads(args.similarity_data.read())
            ]
            for offliner_definition in session.scalars(
                select(OfflinerDefinition).where(
                    OfflinerDefinition.offliner == args.offliner
                )
            ):
                # update the spec for the offliner definition to use the new
                # similarity data transformers list
                offliner_spec = OfflinerSpecSchema.model_validate(
                    offliner_definition.schema
                )
                offliner_spec.similarity_data = similarity_data
                # update the db offliner definition and all of its associated recipes
                offliner_definition.schema = offliner_spec.model_dump(mode="json")
                nb_recipes_modified = update_recipes(
                    session,
                    offliner=offliner,
                    offliner_definition=create_offliner_definition_schema(
                        offliner_definition
                    ),
                )
                logger.info(f"updated {nb_recipes_modified} recipe(s) ")

    logger.info("FINISH!")
