from marshmallow import fields

from common.schemas import SerializableSchema, String
from common.schemas.fields import validate_zim_description, validate_zim_title


class GutenbergFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    languages = String(
        metadata={
            "label": "Languages",
            "description": (
                "Comma-separated list of lang codes to filter "
                "export to (preferably ISO 639-1, else ISO 639-3) Defaults to all"
            ),
        },
    )

    formats = String(
        metadata={
            "label": "Formats",
            "description": (
                "Comma-separated list of formats to filter export to (epub,"
                " html, pdf, all) Defaults to all"
            ),
        },
    )

    zim_title = String(
        metadata={
            "label": "Title",
            "description": "Custom title for your project and ZIM.",
        },
        data_key="zim-title",
        validate=validate_zim_title,
    )

    zim_desc = String(
        metadata={"label": "Description", "description": "Description for ZIM"},
        data_key="zim-desc",
        validate=validate_zim_description,
    )

    books = String(
        metadata={
            "label": "Books",
            "description": (
                "Filter to only specific books ; separated by commas, or dashes "
                "for intervals. Defaults to all"
            ),
        },
    )

    concurrency = fields.Integer(
        metadata={
            "label": "Concurrency",
            "description": "Number of concurrent threads to use",
        },
    )

    dlc = fields.Integer(
        metadata={
            "label": "Download Concurrency",
            "description": (
                "Number of parallel downloads to run (overrides concurrency)"
            ),
        },
        data_key="dlc",
    )

    # /!\ we are using a boolean flag for this while the actual option
    # expect an output folder for the ZIM files.
    # Given we can't set the output dir for regular mode, we're using this
    # flag to switch between the two and the path is set to the mount point
    # in command_for() (offliners.py)
    one_language_one_zim = fields.Boolean(
        truthy=[True, "/output"],
        falsy=[False],
        metadata={
            "label": "Multiple ZIMs",
            "description": "Create one ZIM per language",
        },
        data_key="one-language-one-zim",
    )

    no_index = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "No Index",
            "description": "Do not create full-text index within ZIM file",
        },
        data_key="no-index",
    )

    title_search = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Title search",
            "description": "Search by title feature (⚠️ does not scale)",
        },
        data_key="title-search",
    )

    bookshelves = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Bookshelves",
            "description": "Browse by bookshelves feature",
        },
    )

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": "S3 Storage URL including credentials and bucket",
            "secret": True,
        },
        data_key="optimization-cache",
    )

    use_any_optimized_version = fields.Boolean(
        truthy=[True], falsy=[False], data_key="--use-any-optimized-version"
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        }
    )
