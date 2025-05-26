from pydantic import Field
from pydantic.types import AnyUrl

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    ZIMDescription,
    ZIMFileName,
    ZIMOutputFolder,
    ZIMTitle,
)


class NautilusFlagsSchema(BaseModel):
    archive: AnyUrl | None = Field(
        title="Archive",
        description="URL to a ZIP archive containing all the documents",
        default=None,
    )
    collection: AnyUrl | None = Field(
        title="Custom Collection",
        description=(
            "Different collection JSON URL. Otherwise using `collection.json` "
            "from archive"
        ),
        default=None,
    )

    name: NotEmptyString = Field(
        title="ZIM Name",
        description="Used as identifier and filename (date will be appended)",
        default="mycontent_eng_all",
    )

    pagination: int = Field(
        title="Pagination",
        description="Number of items per page (10 otherwise)",
        default=10,
    )

    no_random: bool = Field(
        title="No-random",
        description="Don't randomize items in list",
        alias="no-random",
    )

    show_description: bool = Field(
        title="Show descriptions",
        description="Show items's descriptions in main list",
        alias="show-description",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description=(
            "Output folder for ZIM file or build folder. Leave it as `/output`"
        ),
        default="/output",
        validate_default=True,
    )
    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided)",
        alias="zim-file",
    )
    language: NotEmptyString = Field(
        title="Language",
        description="ISO-639-3 (3 chars) language code of content",
    )
    locale: NotEmptyString = Field(
        title="Locale",
        description=(
            "Locale name to use for translations (if avail) and time "
            "representations. Defaults to --language or English."
        ),
    )
    title: ZIMTitle = Field(
        title="Title",
        description="Title for your project and ZIM. Otherwise --name.",
    )
    description: ZIMDescription = Field(
        title="Description",
        description="Description for your project and ZIM.",
    )

    creator: NotEmptyString = Field(
        title="Content Creator",
        description="Name of content creator.",
        default="Nautilus",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description="List of comma-separated Tags for the ZIM file.",
    )

    main_logo: AnyUrl = Field(
        title="Header Logo",
        description=("Custom logo. Will be resized to 300x65px. Nautilus otherwise."),
        alias="main-logo",
        default="Nautilus",
    )
    secondary_logo: AnyUrl | None = Field(
        title="Footer logo",
        description=("Custom footer logo. Will be resized to 300x65px. None otherwise"),
        alias="secondary-logo",
        default=None,
    )

    favicon: AnyUrl = Field(
        title="Favicon",
        description=("Custom favicon. Will be resized to 48x48px. Nautilus otherwise."),
    )
    main_color: NotEmptyString = Field(
        title="Main Color",
        description=(
            "Custom header color. Hex/HTML syntax (#DEDEDE). Default to main-logo's"
            " primary color solarized (or #95A5A6 if no logo)."
        ),
        alias="main-color",
    )
    secondary_color: NotEmptyString = Field(
        title="Secondary Color",
        description=(
            "Custom footer color. Hex/HTML syntax (#DEDEDE). Default to main-logo's"
            " primary color solarized (or #95A5A6 if no logo)."
        ),
        alias="secondary-color",
    )
    about: AnyUrl = Field(
        title="About page",
        description="Custom about HTML page.",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )


class NautilusFlagsSchemaRelaxed(NautilusFlagsSchema):
    """A Nautils flags schema with relaxed constraints on validation

    For now, only zim_file name is not checked anymore.
    Typically used for nautilus.kiwix.org
    """

    zim_file: NotEmptyString = Field(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided).",
        alias="zim-file",
    )
