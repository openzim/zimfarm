from typing import Literal

from pydantic import AnyUrl, Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    OptionalNotEmptyString,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMOutputFolder,
    OptionalZIMTitle,
)


class NautilusFlagsSchema(DashModel):
    offliner_id: Literal["nautilus"]

    archive: AnyUrl | None = OptionalField(
        title="Archive",
        description="URL to a ZIP archive containing all the documents",
    )
    collection: AnyUrl | None = OptionalField(
        title="Custom Collection",
        description=(
            "Different collection JSON URL. Otherwise using `collection.json` "
            "from archive"
        ),
    )

    name: NotEmptyString = Field(
        title="ZIM Name",
        description="Used as identifier and filename (date will be appended)",
    )

    pagination: int | None = OptionalField(
        title="Pagination",
        description="Number of items per page (10 otherwise)",
    )

    no_random: bool | None = OptionalField(
        title="No-random",
        description="Don't randomize items in list",
    )

    show_description: bool | None = OptionalField(
        title="Show descriptions",
        description="Show items's descriptions in main list",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description=(
            "Output folder for ZIM file or build folder. Leave it as `/output`"
        ),
    )
    zim_file: OptionalZIMFileName = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided)",
    )
    language: OptionalNotEmptyString = OptionalField(
        title="Language",
        description="ISO-639-3 (3 chars) language code of content",
    )
    locale: OptionalNotEmptyString = OptionalField(
        title="Locale",
        description=(
            "Locale name to use for translations (if avail) and time "
            "representations. Defaults to --language or English."
        ),
    )
    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Title for your project and ZIM. Otherwise --name.",
    )
    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Description for your project and ZIM.",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Content Creator",
        description="Name of content creator.",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description='Custom publisher name (ZIM metadata). "openZIM" otherwise',
    )

    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="List of comma-separated Tags for the ZIM file.",
    )

    main_logo: AnyUrl | None = OptionalField(
        title="Header Logo",
        description=("Custom logo. Will be resized to 300x65px. Nautilus otherwise."),
    )
    secondary_logo: AnyUrl | None = OptionalField(
        title="Footer logo",
        description=("Custom footer logo. Will be resized to 300x65px. None otherwise"),
    )

    favicon: AnyUrl | None = OptionalField(
        title="Favicon",
        description=("Custom favicon. Will be resized to 48x48px. Nautilus otherwise."),
    )
    main_color: OptionalNotEmptyString = OptionalField(
        title="Main Color",
        description=(
            "Custom header color. Hex/HTML syntax (#DEDEDE). Default to main-logo's"
            " primary color solarized (or #95A5A6 if no logo)."
        ),
    )
    secondary_color: OptionalNotEmptyString = OptionalField(
        title="Secondary Color",
        description=(
            "Custom footer color. Hex/HTML syntax (#DEDEDE). Default to main-logo's"
            " primary color solarized (or #95A5A6 if no logo)."
        ),
    )
    about: AnyUrl | None = OptionalField(
        title="About page",
        description="Custom about HTML page.",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )


class NautilusFlagsSchemaRelaxed(NautilusFlagsSchema):
    """A Nautils flags schema with relaxed constraints on validation

    For now, only zim_file name is not checked anymore.
    Typically used for nautilus.kiwix.org
    """

    zim_file: OptionalNotEmptyString = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided).",
    )
