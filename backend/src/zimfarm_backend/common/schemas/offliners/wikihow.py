from marshmallow import fields, validate

from common.schemas import SerializableSchema, String
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
    validate_zim_title,
)


class WikihowFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    language = String(
        metadata={
            "label": "Language",
            "description": "wikiHow website to build from. 2-letters language code.",
        },
        required=True,
    )

    name = String(
        metadata={
            "label": "Name",
            "description": "ZIM name. Used as identifier and filename "
            "(date will be appended). Constructed from language if not supplied",
        },
    )

    title = String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. "
            "Wikihow homepage title otherwise",
        },
        validate=validate_zim_title,
    )

    description = String(
        metadata={
            "label": "Description",
            "description": "Custom description for your ZIM. "
            "Wikihow homepage description (meta) otherwise",
        },
        validate=validate_zim_description,
    )

    icon = fields.Url(
        metadata={
            "label": "Icon",
            "description": "Custom Icon for your ZIM (URL). "
            "wikiHow square logo otherwise",
        }
    )

    creator = String(
        metadata={
            "label": "Creator",
            "description": "Name of content creator. “wikiHow” otherwise",
        },
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        },
    )

    tag = String(
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

    only = fields.Url(
        metadata={
            "label": "Exclude",
            "description": "URL to a text file listing Article IDs. "
            "This filters out every other article. "
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

    tmp_dir = String(
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

    zim_file = String(
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

    category = String(
        metadata={
            "label": "Categories",
            "description": "Only scrape those categories (comma-separated). "
            "Use URL-ID of the Category "
            "(after the colon `:` in the URL). "
            "Add a slash after Category to request it without recursion",
        },
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

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )

    missing_article_tolerance = fields.Integer(
        metadata={
            "label": "Missing tolerance",
            "description": "Allow this percentage (0-100) of articles to "
            "be missing (HTTP 404). Defaults to 0: no tolerance",
        },
        data_key="missing-article-tolerance",
        validate=validate.Range(min=0, max=100),
    )

    delay = fields.Float(
        metadata={
            "label": "Delay",
            "description": "Add this delay (seconds) "
            "before each request to please wikiHow servers. Can be fractions. "
            "Defaults to 0: no delay",
        },
    )

    api_delay = fields.Float(
        metadata={
            "label": "API Delay",
            "description": "Add this delay (seconds) "
            "before each API query (!= calls) to please wikiHow servers. "
            "Can be fractions. Defaults to 0: no delay",
        },
        data_key="api-delay",
    )
