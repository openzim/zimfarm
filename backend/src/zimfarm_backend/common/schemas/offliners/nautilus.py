from marshmallow import fields

from common.schemas import HexColor, SerializableSchema, String
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
    validate_zim_title,
)


class NautilusFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    archive = fields.Url(
        metadata={
            "label": "Archive",
            "description": "URL to a ZIP archive containing all the documents",
        },
        required=False,
    )
    collection = fields.Url(
        metadata={
            "label": "Custom Collection",
            "description": (
                "Different collection JSON URL. Otherwise using `collection.json` "
                "from archive"
            ),
        },
        required=False,
    )

    name = String(
        metadata={
            "label": "ZIM Name",
            "description": "Used as identifier and filename (date will be appended)",
            "placeholder": "mycontent_eng_all",
        },
        required=True,
    )

    pagination = fields.Integer(
        metadata={
            "label": "Pagination",
            "description": "Number of items per page (10 otherwise)",
        },
    )

    no_random = fields.Boolean(
        metadata={"label": "No-random", "description": "Don't randomize items in list"},
        data_key="no-random",
    )

    show_description = fields.Boolean(
        metadata={
            "label": "Show descriptions",
            "description": "Show items's descriptions in main list",
        },
        data_key="show-description",
    )

    output = String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": (
                "Output folder for ZIM file or build folder. Leave it as `/output`"
            ),
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
    )
    zim_file = String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided)",
        },
        data_key="zim-file",
        validate=validate_zim_filename,
    )
    language = String(
        metadata={
            "label": "Language",
            "description": "ISO-639-3 (3 chars) language code of content",
        }
    )
    locale = String(
        metadata={
            "label": "Locale",
            "description": (
                "Locale name to use for translations (if avail) and time "
                "representations. Defaults to --language or English."
            ),
        }
    )
    title = String(
        metadata={
            "label": "Title",
            "description": "Title for your project and ZIM. Otherwise --name.",
        },
        validate=validate_zim_title,
    )
    description = String(
        metadata={
            "label": "Description",
            "description": "Description for your project and ZIM.",
        },
        validate=validate_zim_description,
    )
    creator = String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator.",
        }
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        }
    )

    tags = String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of comma-separated Tags for the ZIM file.",
        }
    )

    main_logo = fields.Url(
        metadata={
            "label": "Header Logo",
            "description": (
                "Custom logo. Will be resized to 300x65px. Nautilus otherwise."
            ),
        },
        data_key="main-logo",
    )
    secondary_logo = fields.Url(
        metadata={
            "label": "Footer logo",
            "description": (
                "Custom footer logo. Will be resized to 300x65px. None otherwise"
            ),
        },
        data_key="secondary-logo",
    )
    favicon = fields.Url(
        metadata={
            "label": "Favicon",
            "description": (
                "Custom favicon. Will be resized to 48x48px. Nautilus otherwise."
            ),
        },
    )
    main_color = HexColor(
        metadata={
            "label": "Main Color",
            "description": (
                "Custom header color. Hex/HTML syntax (#DEDEDE). Default to main-logo's"
                " primary color solarized (or #95A5A6 if no logo)."
            ),
        },
        data_key="main-color",
    )
    secondary_color = HexColor(
        metadata={
            "label": "Secondary Color",
            "description": (
                "Custom footer color. Hex/HTML syntax (#DEDEDE). Default to main-logo's"
                " primary color solarized (or #95A5A6 if no logo)."
            ),
        },
        data_key="secondary-color",
    )
    about = fields.Url(
        metadata={
            "label": "About page",
            "description": "Custom about HTML page.",
        },
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )


class NautilusFlagsSchemaRelaxed(NautilusFlagsSchema):
    """A Nautils flags schema with relaxed constraints on validation

    For now, only zim_file name is not checked anymore.
    Typically used for nautilus.kiwix.org
    """

    zim_file = String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided).",
        },
        data_key="zim-file",
    )
