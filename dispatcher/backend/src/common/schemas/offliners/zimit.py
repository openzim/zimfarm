from marshmallow import fields

from common.schemas import SerializableSchema
from common.schemas.fields import validate_output


class ZimitFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    url = fields.Url(
        metadata={
            "label": "URL",
            "description": "The URL to start crawling from and main page for ZIM",
        },
        required=True,
    )

    name = fields.String(
        metadata={
            "label": "Name",
            "description": "Name of the ZIM. "
            "Used to compose filename if not otherwise defined",
        },
        required=True,
    )

    lang = fields.String(
        metadata={
            "label": "Language",
            "description": "ISO-639-3 (3 chars) language code of content. "
            "Default to `eng`",
        }
    )

    title = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom title for ZIM. Default to title of main page",
        }
    )
    description = fields.String(
        metadata={"label": "Description", "description": "Description for ZIM"}
    )

    favicon = fields.Url(
        metadata={
            "label": "Favicon",
            "description": "URL for Favicon. "
            "If unspecified, will attempt to use the one used from main page.",
        },
        required=False,
    )

    zim_file = fields.String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided)",
        },
        data_key="zim-file",
    )

    tags = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of Tags for the ZIM file.",
        }
    )

    creator = fields.String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator.",
        }
    )

    source = fields.String(
        metadata={
            "label": "Content Source",
            "description": "Source name/URL of content",
        }
    )

    workers = fields.Integer(
        metadata={
            "label": "Workers",
            "description": "The number of workers to run in parallel. Default to 1",
        },
        required=False,
    )

    include_domains = fields.String(
        metadata={
            "label": "Include domains",
            "description": "Limit to URLs from only certain domains. "
            "If not set, all URLs are included.",
        },
        data_key="include-domains",
        required=False,
    )

    exclude = fields.String(
        metadata={
            "label": "Exclude",
            "description": "Regex of URLs that should be excluded from the crawl.",
        },
        required=False,
    )

    wait_until = fields.String(
        metadata={
            "label": "WaitUntil",
            "description": "Puppeteer page.goto() condition to wait for "
            "before continuing. Default to `load`",
        },
        data_key="waitUntil",
        required=False,
    )

    limit = fields.Integer(
        metadata={
            "label": "Limit",
            "description": "Limit crawl to this number of pages. 0 means no-limit.",
        },
    )

    timeout = fields.Integer(
        metadata={
            "label": "Timeout",
            "description": "Timeout for each page to load (in millis). "
            "Default to 30000",
        },
        required=False,
    )

    scope = fields.String(
        metadata={
            "label": "Scope",
            "description": "The scope of current page that should be included in the "
            "crawl (defaults to the domain of URL)",
        },
        required=False,
    )

    scroll = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Scroll",
            "description": "If set, will autoscroll pages to bottom.",
        },
        required=False,
    )

    verbose = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Verbose mode",
            "description": "Whether to display additional logs",
        },
        required=False,
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

    replay_viewer_source = fields.Url(
        metadata={
            "label": "Replay Viewer Source",
            "description": "URL from which to load the ReplayWeb.page "
            "replay viewer from",
        },
        data_key="replay-viewer-source",
        required=False,
    )
