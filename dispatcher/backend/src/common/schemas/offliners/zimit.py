from marshmallow import fields, validate

from common.schemas import SerializableSchema, StringEnum
from common.schemas.fields import validate_output, validate_zim_filename


# https://github.com/puppeteer/puppeteer/blob/main/src/common/DeviceDescriptors.ts
validate_devicelist = validate.OneOf(
    sorted(
        [
            "Blackberry PlayBook",
            "Blackberry PlayBook landscape",
            "BlackBerry Z30",
            "BlackBerry Z30 landscape",
            "Galaxy Note 3",
            "Galaxy Note 3 landscape",
            "Galaxy Note II",
            "Galaxy Note II landscape",
            "Galaxy S III",
            "Galaxy S III landscape",
            "Galaxy S5",
            "Galaxy S5 landscape",
            "iPad",
            "iPad landscape",
            "iPad Mini",
            "iPad Mini landscape",
            "iPad Pro",
            "iPad Pro landscape",
            "iPhone 4",
            "iPhone 4 landscape",
            "iPhone 5",
            "iPhone 5 landscape",
            "iPhone 6",
            "iPhone 6 landscape",
            "iPhone 6 Plus",
            "iPhone 6 Plus landscape",
            "iPhone 7",
            "iPhone 7 landscape",
            "iPhone 7 Plus",
            "iPhone 7 Plus landscape",
            "iPhone 8",
            "iPhone 8 landscape",
            "iPhone 8 Plus",
            "iPhone 8 Plus landscape",
            "iPhone SE",
            "iPhone SE landscape",
            "iPhone X",
            "iPhone X landscape",
            "iPhone XR",
            "iPhone XR landscape",
            "iPhone 11",
            "iPhone 11 landscape",
            "iPhone 11 Pro",
            "iPhone 11 Pro landscape",
            "iPhone 11 Pro Max",
            "iPhone 11 Pro Max landscape",
            "JioPhone 2",
            "JioPhone 2 landscape",
            "Kindle Fire HDX",
            "Kindle Fire HDX landscape",
            "LG Optimus L70",
            "LG Optimus L70 landscape",
            "Microsoft Lumia 550",
            "Microsoft Lumia 950",
            "Microsoft Lumia 950 landscape",
            "Nexus 10",
            "Nexus 10 landscape",
            "Nexus 4",
            "Nexus 4 landscape",
            "Nexus 5",
            "Nexus 5 landscape",
            "Nexus 5X",
            "Nexus 5X landscape",
            "Nexus 6",
            "Nexus 6 landscape",
            "Nexus 6P",
            "Nexus 6P landscape",
            "Nexus 7",
            "Nexus 7 landscape",
            "Nokia Lumia 520",
            "Nokia Lumia 520 landscape",
            "Nokia N9",
            "Nokia N9 landscape",
            "Pixel 2",
            "Pixel 2 landscape",
            "Pixel 2 XL",
            "Pixel 2 XL landscape",
        ]
    )
)


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
        validate=validate_zim_filename,
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

    new_context = StringEnum(
        metadata={
            "label": "New Context",
            "description": "The context for each new capture. Defaults to page",
        },
        validate=validate.OneOf(["page", "session", "browser"]),
        data_key="newContext",
        required=False,
    )

    custom_css = fields.Url(
        metadata={
            "label": "Custom CSS",
            "description": "URL to a CSS file to inject into pages",
        },
        data_key="custom-css",
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

    stats_filename = fields.String(
        metadata={
            "label": "Stats filename",
            "placeholder": "/output/task_progress.json",
            "description": "Scraping progress file. "
            "Leave it as `/output/task_progress.json`",
        },
        data_key="statsFilename",
        missing="/output/task_progress.json",
        default="/output/task_progress.json",
        validate=validate.Equal("/output/task_progress.json"),
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

    use_sitemap = fields.Url(
        metadata={
            "label": "Use sitemap",
            "description": "Use as sitemap to get additional URLs for the crawl "
            "(usually at /sitemap.xml)",
        },
        data_key="useSitemap",
        required=False,
    )

    mobile_device = StringEnum(
        metadata={
            "label": "As device",
            "description": "Device to crawl as. Defaults to `Iphone X`. "
            "See Pupeeter's DeviceDescriptors.",
        },
        data_key="mobileDevice",
        required=False,
        validate=validate_devicelist,
    )

    admin_email = fields.String(
        metadata={
            "label": "Admin Email",
            "description": "Admin Email for crawler: used in UserAgent "
            "so website admin can contact us",
        },
        data_key="adminEmail",
        required=False,
    )
