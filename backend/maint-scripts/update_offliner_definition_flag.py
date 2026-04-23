#!/usr/bin/env python3

"""
Script to update an offliner definition's flag property in the database.

EXAMPLES:

1. Update the 'allow_remote_url' property of the 'articleList' flag to true for all
    versions of an offliner:
   ./update_offliner_definition_flag.py -o mwoffliner -f articleList \
        -p allow_remote_url -v true --type boolean
"""

import argparse
from copy import deepcopy

import sqlalchemy as sa
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend import logger
from zimfarm_backend.common.constants import parse_bool
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import OfflinerDefinition
from zimfarm_backend.db.offliner_definition import create_offliner_definition_schema

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update offliner definition flag properties in the database",
    )

    parser.add_argument(
        "-o", "--offliner", required=True, help="Specify which offliner to update"
    )

    parser.add_argument(
        "-f",
        "--flag",
        required=True,
        help="Specify the flag to update (e.g., articleList)",
    )

    parser.add_argument(
        "-p",
        "--property",
        required=True,
        help="Specify the property to update (e.g., allow_remote_url)",
    )

    parser.add_argument(
        "-v", "--value", required=True, help="The new value for the property"
    )

    parser.add_argument(
        "-t",
        "--type",
        required=True,
        choices=["string", "boolean", "integer", "float"],
        help="The type of the new value",
    )

    args = parser.parse_args()

    # Convert value based on type
    if args.type == "string":
        value = args.value
    elif args.type == "boolean":
        value = parse_bool(args.value)
    elif args.type == "integer":
        value = int(args.value)
    elif args.type == "float":
        value = float(args.value)
    else:
        raise ValueError(f"Unknown type: {args.type}")

    with Session.begin() as session:
        definitions = (
            session.execute(
                sa.select(OfflinerDefinition).where(
                    OfflinerDefinition.offliner == args.offliner
                )
            )
            .scalars()
            .all()
        )
        for offliner_definition in definitions:
            logger.info(
                f"Processing {offliner_definition.offliner} version "
                f"{offliner_definition.version}"
            )
            flags_dict = deepcopy(offliner_definition.schema["flags"])
            if args.flag in flags_dict:
                flags_dict[args.flag][args.property] = value
                offliner_definition.schema["flags"] = flags_dict
                flag_modified(offliner_definition, "schema")
                # Validate that the schema is still valid
                create_offliner_definition_schema(offliner_definition)
                logger.info(
                    f"updated offliner {args.offliner} version "
                    f"{offliner_definition.version} flag '{args.flag}' property "
                    f"'{args.property}' to {value}"
                )
            else:
                logger.warning(
                    f"flag '{args.flag}' not found in offliner {args.offliner} version "
                    f"{offliner_definition.version}"
                )

    logger.info("FINISH!")
