#!/usr/bin/env python3

"""
Script to update similarity data of offliner definitions and schedules

EXAMPLES:

1. Update the similarity data for all offliner definitions. This updates the recipes
   similarity data too. Input can be a JSON file or sent via stdin.
   ./update_scraper_version.py -o mwoffliner -s simialrity_data.in

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
    | ./update_scraper_version.py \
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
from zimfarm_backend.db.models import OfflinerDefinition, Schedule
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
)
from zimfarm_backend.db.schedule import create_schedule_full_schema


def update_schedules(
    session: OrmSession,
    *,
    offliner: OfflinerSchema,
    offliner_definition: OfflinerDefinitionSchema,
) -> int:
    nb_modified: int = 0

    for schedule in session.execute(
        sa.select(Schedule).where(
            Schedule.config["offliner"]["offliner_id"].astext == offliner.id,
            Schedule.offliner_definition_id == offliner_definition.id,
        )
    ).scalars():
        logger.info(f"seting similarity data for schedule {schedule.name}")
        schedule.similarity_data = generate_similarity_data(
            schedule.config["offliner"], offliner, offliner_definition.schema_
        )
        flag_modified(schedule, "config")
        create_schedule_full_schema(schedule, offliner)
        nb_modified += 1
    return nb_modified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update schedules and requested tasks image tag "
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
                nb_schedules_modified = update_schedules(
                    session,
                    offliner=offliner,
                    offliner_definition=create_offliner_definition_schema(
                        offliner_definition
                    ),
                )
                logger.info(f"updated {nb_schedules_modified} schedule(s) ")

    logger.info("FINISH!")
