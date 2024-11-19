from marshmallow import fields, validate

from common.schemas import SerializableSchema, String
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_longdescription,
    validate_zim_title,
)


class MindtouchFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    library_url = String(
        metadata={
            "label": "Library URL",
            "description": "URL of the Mindtouch / Nice CXone Expert instance (must NOT"
            " contain trailing slash), e.g. for LibreTexts Geosciences it is "
            "https://geo.libretexts.org",
        },
        data_key="library-url",
        required=True,
    )

    creator = String(
        metadata={
            "label": "Creator",
            "description": "Name of content creator",
        },
        required=True,
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        },
    )

    file_name = String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM filename. Do not input trailing `.zim`, it "
            "will be automatically added. Defaults to {name}_{period}",
        },
        data_key="file-name",
    )

    name = String(
        metadata={
            "label": "ZIM name",
            "description": "Name of the ZIM.",
        },
        required=True,
    )

    title = String(
        metadata={
            "label": "ZIM title",
            "description": "Title of the ZIM.",
        },
        validate=validate_zim_title,
        required=True,
    )

    description = String(
        metadata={
            "label": "ZIM description",
            "description": "Description of the ZIM.",
        },
        validate=validate_zim_description,
        required=True,
    )

    long_description = String(
        metadata={
            "label": "ZIM long description",
            "description": "Long description of the ZIM.",
        },
        data_key="long-description",
        validate=validate_zim_longdescription,
    )

    tags = String(
        metadata={
            "label": "ZIM Tags",
            "description": "A semicolon (;) delimited list of tags to add to the ZIM.",
        }
    )

    secondary_color = String(
        metadata={
            "label": "Secondary color",
            "description": "Secondary (background) color of ZIM UI. Default: '#FFFFFF'",
        },
        data_key="secondary-color",
    )

    page_id_include = String(
        metadata={
            "label": "Page ID include",
            "description": "CSV of page ids to include. Parent pages will be included "
            "as well for proper navigation, up to root (or subroot if --root-page-id is"
            " set). Can be combined with --page-title-include (pages with matching "
            "title or id will be included)",
        },
        data_key="page-id-include",
    )

    page_title_include = String(
        metadata={
            "label": "Page title include regex",
            "description": "Includes only pages with title matching the given regular "
            "expression, and their parent pages for proper navigation, up to root (or "
            "subroot if --root-page-id is set). Can be combined with --page-id-include "
            "(pages with matching title or id will be included)",
        },
        data_key="page-title-include",
    )

    page_title_exclude = String(
        metadata={
            "label": "Page title exclude regex",
            "description": "Excludes pages with title matching the given regular "
            "expression",
        },
        data_key="page-title-exclude",
    )

    root_page_id = String(
        metadata={
            "label": "Root page ID",
            "description": "ID of the root page to include in ZIM. Only this page and "
            "its subpages will be included in the ZIM",
        },
        data_key="root-page-id",
    )

    illustration_url = String(
        metadata={
            "label": "Illustration URL",
            "description": "URL to illustration to use for ZIM illustration and "
            "favicon",
        },
        data_key="illustration-url",
    )

    optimization_cache = String(
        metadata={
            "label": "Optimization Cache URL",
            "description": "S3 Storage URL including credentials and bucket",
            "secret": True,
        },
        data_key="optimization-cache",
    )

    assets_workers = fields.Integer(
        metadata={
            "label": "Asset workers",
            "description": "Number of parallel workers for asset processing. Default: "
            "10",
        },
        required=False,
        data_key="assets-workers",
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )

    stats_filename = String(
        metadata={
            "label": "Stats filename",
            "placeholder": "/output/task_progress.json",
            "description": "Scraping progress file. "
            "Leave it as `/output/task_progress.json`",
        },
        data_key="stats-filename",
        load_default="/output/task_progress.json",
        dump_default="/output/task_progress.json",
        validate=validate.Equal("/output/task_progress.json"),
    )

    output = String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file(s). Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
    )
