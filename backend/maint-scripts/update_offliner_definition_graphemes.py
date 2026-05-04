#!/usr/bin/env python3

import argparse
from copy import deepcopy
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import OfflinerDefinition
from zimfarm_backend.db.offliner_definition import create_offliner_definition_schema


def update_flag(
    flags_dict: dict[str, Any], *, flag_name: str, old_key: str, new_key: str
) -> bool:
    flag_changed = False

    if old_key in flags_dict[flag_name]:
        flags_dict[flag_name][new_key] = flags_dict[flag_name][old_key]
        del flags_dict[flag_name][old_key]
        flag_changed = True
        if flag_changed:
            logger.info(
                f"Schema modified for {offliner_definition.offliner} "
                f"v{offliner_definition.version} flag '{flag_name}'"
            )

    return flag_changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
Update offliner definition schemas: minLength -> minGraphemes, maxLength -> maxGraphemes
""",
    )

    args = parser.parse_args()

    with Session.begin() as session:
        definitions = session.execute(select(OfflinerDefinition)).scalars().all()
        for offliner_definition in definitions:
            logger.info(
                f"Processing {offliner_definition.offliner} version "
                f"{offliner_definition.version}"
            )
            flags_dict = deepcopy(offliner_definition.schema["flags"])

            offliner_modified = False
            for flag in flags_dict:
                update_flag(
                    flags_dict,
                    flag_name=flag,
                    old_key="min_length",
                    new_key="min_graphemes",
                )

                update_flag(
                    flags_dict,
                    flag_name=flag,
                    old_key="max_length",
                    new_key="max_graphemes",
                )

                update_flag(
                    flags_dict,
                    flag_name=flag,
                    old_key="relaxed_min_length",
                    new_key="relaxed_min_graphemes",
                )

                update_flag(
                    flags_dict,
                    flag_name=flag,
                    old_key="relaxed_max_length",
                    new_key="relaxed_max_graphemes",
                )

            offliner_definition.schema["flags"] = flags_dict
            flag_modified(offliner_definition, "schema")
            # Validate that the schema is still valid
            create_offliner_definition_schema(offliner_definition)
            logger.info(
                f"Schema modified for {offliner_definition.offliner} "
                f"v{offliner_definition.version}"
            )

    logger.info("FINISH!")
