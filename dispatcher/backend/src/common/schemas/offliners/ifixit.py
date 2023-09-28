from marshmallow import fields, validate

from common.schemas import SerializableSchema
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
)


def validate_percent(value):
    return value >= 1 and value <= 100


class IFixitFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    language = fields.String(
        metadata={
            "label": "Language",
            "description": "iFixIt website to build from",
        },
        required=True,
    )

    name = fields.String(
        metadata={
            "label": "Name",
            "description": "ZIM name. Used as identifier and filename "
            "(date will be appended). Constructed from language if not supplied",
        },
    )

    title = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. "
            "iFixIt homepage title otherwise",
        },
    )

    description = fields.String(
        metadata={
            "label": "Description",
            "description": "Custom description for your ZIM. "
            "iFixIt homepage description (meta) otherwise",
        },
        validate=validate_zim_description,
    )

    icon = fields.Url(
        metadata={
            "label": "Icon",
            "description": "Custom Icon for your ZIM (URL). "
            "iFixit square logo otherwise",
        }
    )

    creator = fields.String(
        metadata={
            "label": "Creator",
            "description": "Name of content creator. “iFixit” otherwise",
        },
    )

    publisher = fields.String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        },
    )

    tag = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of semi-colon-separated Tags for the ZIM file. "
            "_category:ifixit and ifixit added automatically",
        }
    )

    output = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file(s). Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
    )

    tmp_dir = fields.String(
        metadata={
            "label": "Temp folder",
            "placeholder": "/output",
            "description": "Where to create temporay build folder. "
            "Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
        data_key="tmp-dir",
    )

    zim_file = fields.String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided). "
            "Include {period} to insert date period dynamically",
        },
        data_key="zim-file",
        validate=validate_zim_filename,
    )

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": "S3 Storage URL including credentials and bucket",
            "secret": True,
        },
        data_key="optimization-cache",
    )

    stats_filename = fields.String(
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

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )

    delay = fields.Float(
        metadata={
            "label": "Delay",
            "description": "Add this delay (seconds) "
            "before each request to please iFixit servers. Can be fractions. "
            "Defaults to 0: no delay",
        },
    )

    api_delay = fields.Float(
        metadata={
            "label": "API Delay",
            "description": "Add this delay (seconds) "
            "before each API query (!= calls) to please iFixit servers. "
            "Can be fractions. Defaults to 0: no delay",
        },
        data_key="api-delay",
    )

    cdn_delay = fields.Float(
        metadata={
            "label": "CDN Delay",
            "description": "Add this delay (seconds) "
            "before each CDN file download to please iFixit servers. "
            "Can be fractions. Defaults to 0: no delay",
        },
        data_key="cdn-delay",
    )

    max_missing_items = fields.Integer(
        metadata={
            "label": "Max Missing Items",
            "description": "Amount of missing items which will force the scraper to "
            "stop, expressed as a percentage of the total number of items to retrieve. "
            "Integer from 1 to 100",
        },
        data_key="max-missing-items-percent",
        validate=validate_percent,
    )

    max_error_items = fields.Integer(
        metadata={
            "label": "Max Error Items",
            "description": "Amount of items with failed processing which will force "
            "the scraper to stop, expressed as a percentage of the total number of "
            "items to retrieve. Integer from 1 to 100",
        },
        data_key="max-error-items-percent",
        validate=validate_percent,
    )

    category = fields.String(
        metadata={
            "label": "Categories",
            "description": "Only scrape those categories (comma-separated). "
            "Specify the category names",
        }
    )

    no_category = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "No category", "description": "Do not scrape any category"},
        data_key="no-category",
    )

    guide = fields.String(
        metadata={
            "label": "Guides",
            "description": "Only scrape this guide (comma-separated)). "
            "Specify the guide names",
        },
    )

    no_guide = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "No guide", "description": "Do not scrape any guide"},
        data_key="no-guide",
    )

    info = fields.String(
        metadata={
            "label": "Info",
            "description": "Only scrape this info (comma-separated)). "
            "Specify the info names",
        },
    )

    no_info = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "No info", "description": "Do not scrape any info"},
        data_key="no-info",
    )
