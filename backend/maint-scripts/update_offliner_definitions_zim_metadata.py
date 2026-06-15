#!/usr/bin/env python3


from sqlalchemy import select

from zimfarm_backend import logger
from zimfarm_backend.common.schemas.offliners.models import (
    OfflinerSpecSchema,
    ZimMetadata,
)
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import OfflinerDefinition
from zimfarm_backend.db.offliner_definition import create_offliner_definition_schema

zim_metadata_mapping: dict[str, list[ZimMetadata]] = {
    "devdocs": [
        ZimMetadata(metadata="Name", flag="name_format"),
        ZimMetadata(metadata="Title", flag="title_format"),
        ZimMetadata(metadata="Description", flag="description_format"),
        ZimMetadata(metadata="LongDescription", flag="long_description_format"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Illustration", flag="logo_format"),
    ],
    "freecodecamp": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="LongDescription", flag="long_description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Illustration", flag="illustration"),
    ],
    "gutenberg": [
        ZimMetadata(metadata="Name", flag="zim_name"),
        ZimMetadata(metadata="Title", flag="zim_title"),
        ZimMetadata(metadata="Description", flag="zim_desc"),
        ZimMetadata(metadata="LongDescription", flag="zim_long_desc"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Language", flag="zim_languages"),
    ],
    "ifixit": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Illustration", flag="icon"),
    ],
    "kolibri": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="LongDescription", flag="long_description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Language", flag="lang"),
        ZimMetadata(metadata="Illustration", flag="favicon"),
    ],
    "maps": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="LongDescription", flag="long_description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Illustration", flag="illustration_url"),
    ],
    "mindtouch": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="LongDescription", flag="long_description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Illustration", flag="illustration_url"),
    ],
    "mwoffliner": [
        ZimMetadata(metadata="Name", flag="filenamePrefix"),
        ZimMetadata(metadata="Title", flag="customZimTitle"),
        ZimMetadata(metadata="Description", flag="customZimDescription"),
        ZimMetadata(metadata="LongDescription", flag="customZimLongDescription"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Language", flag="customZimLanguage"),
        ZimMetadata(metadata="Illustration", flag="customZimFavicon"),
        ZimMetadata(metadata="Flavour", flag="formats"),
    ],
    "nautilus": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Language", flag="language"),
        ZimMetadata(metadata="Illustration", flag="favicon"),
    ],
    "openedx": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Illustration", flag="favicon_url"),
    ],
    "phet": [],
    "sotoki": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Illustration", flag="favicon"),
    ],
    "ted": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="LongDescription", flag="long_description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
    ],
    "youtube": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="LongDescription", flag="long_description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Language", flag="language"),
        ZimMetadata(metadata="Illustration", flag="profile"),
    ],
    "zimit": [
        ZimMetadata(metadata="Name", flag="name"),
        ZimMetadata(metadata="Title", flag="title"),
        ZimMetadata(metadata="Description", flag="description"),
        ZimMetadata(metadata="LongDescription", flag="long_description"),
        ZimMetadata(metadata="Creator", flag="creator"),
        ZimMetadata(metadata="Publisher", flag="publisher"),
        ZimMetadata(metadata="Language", flag="zim_lang"),
        ZimMetadata(metadata="Illustration", flag="favicon"),
    ],
}


if __name__ == "__main__":
    with Session.begin() as session:
        for offliner_id, zim_metadata in zim_metadata_mapping.items():
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
                offliner_spec.zim_metadata = zim_metadata
                offliner_definition.schema = offliner_spec.model_dump(mode="json")
                # Validate that the schema is still valid
                create_offliner_definition_schema(offliner_definition)

    logger.info("FINISH!")
