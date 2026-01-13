#!/usr/bin/env python3

import argparse
from typing import Literal

from sqlalchemy import select

from zimfarm_backend import logger
from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import OfflinerDefinition
from zimfarm_backend.db.offliner_definition import create_offliner_definition_schema

FLAG_MAPPINGS: dict[
    str, list[dict[str, Literal["image", "css", "html", "illustration"]]]
] = {
    "devdocs": [{"logo_format": "image"}],
    "freecodecamp": [{"illustration": "image"}],
    "ifixit": [{"icon": "image"}],
    "kolibri": [{"favicon": "image"}, {"css": "css"}, {"about": "html"}],
    "mindtouch": [{"illustration_url": "image"}],
    "mwoffliner": [{"customZimFavicon": "illustration"}],
    "nautilus": [
        {"main_logo": "image"},
        {"secondary_logo": "image"},
        {"favicon": "image"},
        {"about": "html"},
    ],
    "openedx": [{"favicon_url": "image"}],
    "sotoki": [{"favicon": "image"}],
    "youtube": [{"profile": "image"}, {"banner": "image"}],
    "zimit": [{"favicon": "image"}, {"custom_css": "css"}],
}


def update_offliner_definition_flags(
    offliner_id: str,
    spec: OfflinerSpecSchema,
    flag_mappings: list[dict[str, Literal["image", "css", "html", "illustration"]]],
) -> bool:
    """
    Update flags in an offliner definition spec to use blob type with kind.
    """
    modified = False

    for flag_mapping in flag_mappings:
        for flag_name, kind in flag_mapping.items():
            if flag_name not in spec.flags:
                continue

            flag_spec = spec.flags[flag_name]

            if flag_spec.type == "blob" and flag_spec.kind == kind:
                logger.info(
                    f"Flag '{flag_name}' in {offliner_id} already has type=blob "
                    f"and kind={kind}. Skipping..."
                )
                continue

            logger.info(
                f"Changing flag '{flag_name} from {flag_spec.type} ({flag_spec.kind}) "
                f"to blob ({kind})"
            )
            flag_spec.kind = kind
            flag_spec.type = "blob"
            modified = True

    return modified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update offliner definition flags to use blob type with kind",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Do not apply the changes"
    )

    args = parser.parse_args()

    with Session.begin() as session:
        for offliner_id, flag_mappings in FLAG_MAPPINGS.items():
            logger.info(f"Processing offliner: {offliner_id}")

            # Get all definitions for this offliner
            for offliner_definition in session.execute(
                select(OfflinerDefinition).where(
                    OfflinerDefinition.offliner == offliner_id
                )
            ).scalars():
                logger.info(
                    f"Processing {offliner_id} version {offliner_definition.version}"
                )

                offliner_spec = OfflinerSpecSchema.model_validate(
                    offliner_definition.schema
                )

                modified = update_offliner_definition_flags(
                    offliner_id, offliner_spec, flag_mappings
                )

                if modified and not args.dry_run:
                    offliner_definition.schema = offliner_spec.model_dump(mode="json")

                # Validate that the schema is still valid
                create_offliner_definition_schema(offliner_definition)

    logger.info("FINISH!")
