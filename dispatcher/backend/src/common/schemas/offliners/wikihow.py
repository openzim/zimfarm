from marshmallow import fields, validate

from common.schemas import SerializableSchema
from common.schemas.fields import validate_output


class WikihowFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    language = fields.String(
        metadata={
            "label": "Language",
            "description": "wikiHow website to build from. 2-letters language code.",
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
            "Wikihow homepage title otherwise",
        },
    )

    description = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom description for your ZIM. "
            "Wikihow homepage description (meta) otherwise",
        },
    )

    icon = fields.Url(
        metadata={
            "label": "Icon",
            "description": "Custom Icon for your ZIM (URL). "
            "wikiHow square logo otherwise",
        }
    )

    creator = fields.String(
        metadata={
            "label": "Creator",
            "description": "Name of content creator. “wikiHow” otherwise",
        },
    )

    publisher = fields.String(
        metadata={
            "label": "Creator",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        },
    )

    tag = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of semi-colon-separated Tags for the ZIM file. "
            "_category:other and wikihow added automatically",
        }
    )

    without_external_links = fields.Boolean(
        metadata={
            "label": "Without External links",
            "description": "Remove all external links from pages. "
            "Link text is kept but not the address",
        },
        data_key="without-external-links",
    )

    without_videos = fields.Boolean(
        metadata={
            "label": "Without Videos",
            "description": "Don't include the video blocks (Youtube hosted). "
            "Most are copyrighted",
        },
        data_key="without-videos",
        truthy=[True],
        falsy=[False],
    )

    exclude = fields.Url(
        metadata={
            "label": "Exclude",
            "description": "URL to a text file listing Article ID or "
            "`Category:` prefixed Category IDs to exclude from the scrape. "
            "Lines starting with # are ignored",
        },
    )

    low_quality = fields.Boolean(
        metadata={
            "label": "Low quality",
            "description": "Use lower-quality, smaller file-size video encode",
        },
        data_key="low-quality",
    )

    output = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file(s). Leave it as `/output`",
        },
        missing="/output",
        default="/output",
        validate=validate_output,
    )

    tmp_dir = fields.String(
        metadata={
            "label": "Temp folder",
            "placeholder": "/output",
            "description": "Where to create temporay build folder. "
            "Leave it as `/output`",
        },
        missing="/output",
        default="/output",
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
    )

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": "S3 Storage URL including credentials and bucket",
            "secret": True,
        },
        data_key="optimization-cache",
    )

    category = fields.String(
        metadata={
            "label": "Categories",
            "description": "Only scrape those categories (comma-separated). "
            "Use URL-ID of the Category "
            "(after the colon `:` in the URL). "
            "Add a slash after Category to request it without recursion",
        },
    )

    stats_filename = fields.String(
        metadata={
            "label": "Stats filename",
            "placeholder": "/output/task_progress.json",
            "description": "Scraping progress file. "
            "Leave it as `/output/task_progress.json`",
        },
        data_key="stats-filename",
        missing="/output/task_progress.json",
        default="/output/task_progress.json",
        validate=validate.Equal("/output/task_progress.json"),
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )
