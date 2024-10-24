from marshmallow import fields, validate

from common.schemas import SerializableSchema, String, StringEnum
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
    validate_zim_title,
)

# https://github.com/puppeteer/puppeteer/blob/main/src/common/DeviceDescriptors.ts
# https://github.com/puppeteer/puppeteer/blob/
# main/packages/puppeteer-core/src/common/Device.ts
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
            "Galaxy S8",
            "Galaxy S8 landscape",
            "Galaxy S9+",
            "Galaxy S9+ landscape",
            "Galaxy Tab S4",
            "Galaxy Tab S4 landscape",
            "iPad",
            "iPad landscape",
            "iPad (gen 6)",
            "iPad (gen 6) landscape",
            "iPad (gen 7)",
            "iPad (gen 7) landscape",
            "iPad Mini",
            "iPad Mini landscape",
            "iPad Pro",
            "iPad Pro landscape",
            "iPad Pro 11",
            "iPad Pro 11 landscape",
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
            "iPhone 12",
            "iPhone 12 landscape",
            "iPhone 12 Pro",
            "iPhone 12 Pro landscape",
            "iPhone 12 Pro Max",
            "iPhone 12 Pro Max landscape",
            "iPhone 12 Mini",
            "iPhone 12 Mini landscape",
            "iPhone 13",
            "iPhone 13 landscape",
            "iPhone 13 Pro",
            "iPhone 13 Pro landscape",
            "iPhone 13 Pro Max",
            "iPhone 13 Pro Max landscape",
            "iPhone 13 Mini",
            "iPhone 13 Mini landscape",
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
            "Pixel 3",
            "Pixel 3 landscape",
            "Pixel 4",
            "Pixel 4 landscape",
            "Pixel 4a (5G)",
            "Pixel 4a (5G) landscape",
            "Pixel 5",
            "Pixel 5 landscape",
            "Moto G4",
            "Moto G4 landscape",
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

    name = String(
        metadata={
            "label": "Name",
            "description": "Name of the ZIM. "
            "Used to compose filename if not otherwise defined",
        },
        required=True,
    )

    lang = String(
        metadata={
            "label": "Browser Language",
            "description": "If set, sets the language used by the browser, should be"
            "ISO 639 language[-country] code, e.g. `en` or `en-GB`",
        }
    )

    zim_lang = String(
        metadata={
            "label": "ZIM Language",
            "description": "Language metadata of ZIM (warc2zim --lang param). "
            "ISO-639-3 code. Retrieved from homepage if found, fallback to `eng`",
        },
        data_key="zim-lang",
    )

    title = String(
        metadata={
            "label": "Title",
            "description": "Custom title for ZIM. Defaults to title of main page",
        },
        validate=validate_zim_title,
    )

    description = String(
        metadata={"label": "Description", "description": "Description for ZIM"},
        validate=validate_zim_description,
    )

    favicon = fields.Url(
        metadata={
            "label": "Illustration",
            "description": "URL for Illustration. "
            "If unspecified, will attempt to use favicon from main page.",
        },
        required=False,
    )

    zim_file = String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided). "
            "Make sure to end with _{period}.zim",
        },
        data_key="zim-file",
        validate=validate_zim_filename,
    )

    tags = String(
        metadata={
            "label": "ZIM Tags",
            "description": "Single string with individual tags "
            "separated by a semicolon.",
        }
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

    source = String(
        metadata={
            "label": "Content Source",
            "description": "Source name/URL of content",
        }
    )

    workers = fields.Integer(
        metadata={
            "label": "Workers",
            "description": "The number of workers to run in parallel. Defaults to 1",
        },
        required=False,
    )

    wait_until = String(
        metadata={
            "label": "WaitUntil",
            "description": "Puppeteer page.goto() condition to wait for "
            "before continuing. Defaults to `load`",
        },
        data_key="waitUntil",
        required=False,
    )

    depth = fields.Integer(
        metadata={
            "label": "Depth",
            "description": "The depth of the crawl for all seeds. Defaults to -1",
        },
        required=False,
    )

    extra_hops = fields.Integer(
        metadata={
            "label": "Extra Hops",
            "description": "Number of extra 'hops' to follow, "
            "beyond the current scope. Defaults to 0",
        },
        data_key="extraHops",
        required=False,
    )

    limit = fields.Integer(
        metadata={
            "label": "Limit",
            "description": "Limit crawl to this number of pages. 0 means no-limit.",
        },
    )

    max_page_limit = fields.Integer(
        metadata={
            "label": "Max Page Limit",
            "description": "Maximum pages to crawl, overriding pageLimit "
            "if both are set. Defaults to 0",
        },
        required=False,
    )

    scope_type = StringEnum(
        metadata={
            "label": "Scope Type",
            "description": "A predfined scope of the crawl. For more customization, "
            "use 'custom' and set include regexes. Defaults to prefix.",
        },
        data_key="scopeType",
        required=False,
        validate=validate.OneOf(
            ["page", "page-spa", "prefix", "host", "domain", "any", "custom"]
        ),
    )

    include = String(
        metadata={
            "label": "Include",
            "description": "Regex of page URLs that should be "
            "included in the crawl (defaults to the immediate directory of URL)",
        },
        required=False,
    )

    exclude = String(
        metadata={
            "label": "Exclude",
            "description": "Regex of page URLs that should be excluded from the crawl",
        },
        required=False,
    )

    allow_hash_urls = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Allow Hashtag URLs",
            "description": "Allow Hashtag URLs, useful for single-page-application "
            "crawling or when different hashtags load dynamic content",
        },
        data_key="allowHashUrls",
        required=False,
    )

    mobile_device = StringEnum(
        metadata={
            "label": "As device",
            "description": "Device to crawl as. See Pupeeter's Device.ts for a list",
        },
        data_key="mobileDevice",
        required=False,
        validate=validate_devicelist,
    )

    no_mobile_device = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "No device",
            "description": "Do not emulate a device (use at your own risk, behavior is "
            "uncertain ; if set, 'As device' setting is ignored)",
        },
        data_key="noMobileDevice",
        required=False,
    )

    user_agent = String(
        metadata={
            "label": "User Agent",
            "description": "Override user-agent with specified",
        },
        data_key="userAgent",
        required=False,
    )

    user_agent_suffix = String(
        metadata={
            "label": "User Agent Suffix",
            "description": "Append suffix to existing browser user-agent. "
            "Defaults to +Zimit",
        },
        data_key="userAgentSuffix",
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

    behaviors = String(
        metadata={
            "label": "Behaviors",
            "description": "Which background behaviors to enable on each page. "
            "Defaults to autoplay,autofetch,siteSpecific.",
        },
        required=False,
    )

    behavior_timeout = fields.Integer(
        metadata={
            "label": "Behavior Timeout",
            "description": "If >0, timeout (in seconds) for in-page behavior "
            "will run on each page. If 0, a behavior can run until finish. "
            "Defaults to 90",
        },
        data_key="behaviorTimeout",
        required=False,
    )

    delay = fields.Integer(
        metadata={
            "label": "Page Extra Delay",
            "description": "If >0, amount of time to sleep (in seconds) "
            "after behaviors before moving on to next page. Defaults to 0",
        },
        data_key="delay",
        required=False,
    )

    size_limit = fields.Integer(
        metadata={
            "label": "Size Limit",
            "description": "If set, save state and exit "
            "if size limit exceeds this value, in bytes",
        },
        data_key="sizeLimit",
        required=False,
    )

    disk_utilization = fields.Integer(
        metadata={
            "label": "Disk Utilization",
            "description": "Save state and exit if disk utilization exceeds this "
            "percentage value. Default (if not set) is 90%. Set to 0 to disable disk "
            "utilization check.",
        },
        data_key="diskUtilization",
        required=False,
    )

    time_limit = fields.Integer(
        metadata={
            "label": "Time Limit",
            "description": "If set, save state and exit after time limit, in seconds",
        },
        data_key="timeLimit",
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

    keep = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Keep",
            "description": "Should be True. Developer option: must be True if we want "
            "to keep the WARC files for artifacts archiving.",
        },
        required=False,
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

    stats_filename = String(
        metadata={
            "label": "Stats filename",
            "placeholder": "/output/task_progress.json",
            "description": "Scraping progress file. "
            "Leave it as `/output/task_progress.json`",
        },
        data_key="statsFilename",
        load_default="/output/task_progress.json",
        dump_default="/output/task_progress.json",
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

    admin_email = String(
        metadata={
            "label": "Admin Email",
            "description": "Admin Email for crawler: used in UserAgent "
            "so website admin can contact us",
        },
        data_key="adminEmail",
        required=False,
    )

    charsets_to_try = String(
        metadata={
            "label": "Charsets to try",
            "description": "List of charsets to try decode content when charset is not "
            "defined at document or HTTP level. Single string, values separated by a "
            "comma. Default: UTF-8,ISO-8859-1",
        },
        data_key="charsets-to-try",
        required=False,
    )

    ignore_content_header_charsets = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Ignore Content Header Charsets",
            "description": "Ignore the charsets specified in content headers - first "
            "bytes - typically because they are wrong.",
        },
        required=False,
        data_key="ignore-content-header-charsets",
    )

    content_header_bytes_length = fields.Integer(
        metadata={
            "label": "Length of content header",
            "description": "How many bytes to consider when searching for content "
            "charsets in header (default is 1024).",
        },
        required=False,
        data_key="content-header-bytes-length",
    )

    ignore_http_header_charsets = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Ignore HTTP Header Charsets",
            "description": "Ignore the charsets specified in HTTP `Content-Type` "
            "headers, typically because they are wrong.",
        },
        required=False,
        data_key="ignore-http-header-charsets",
    )

    encoding_aliases = String(
        metadata={
            "label": "Encoding aliases",
            "description": "List of encoding/charset aliases to decode WARC content. "
            "Aliases are used when the encoding specified in upstream server exists in"
            " Python under a different name. This parameter has the format "
            "alias_encoding=python_encoding. This parameter is single string, multiple"
            " values are separated by a comma, like in "
            "alias1=encoding1,alias2=encoding2.",
        },
        required=False,
        data_key="encoding-aliases",
    )

    profile = String(
        metadata={
            "label": "Browser profile",
            "description": "Path or HTTP(S) URL to tar.gz file which contains the "
            "browser profile directory for Browsertrix crawler.",
        },
        required=False,
    )

    custom_behaviors = String(
        metadata={
            "label": "Custom behaviors",
            "description": "JS code for custom behaviors to customize crawler. Single "
            "string with individual JS files URL/path separated by a comma.",
        },
        required=False,
        data_key="custom-behaviors",
    )

    warcs = String(
        metadata={
            "label": "WARC files",
            "description": "Directly convert WARC archives to ZIM, by-passing the "
            "crawling phase. This argument must contain the path or HTTP(S) URL to "
            "either warc.gz files or to a tar.gz containing the warc.gz files. "
            "Single value with individual path/URLs separated by comma.",
        },
        required=False,
    )


class ZimitFlagsSchemaRelaxed(ZimitFlagsSchema):
    """A Zimit flags schema with relaxed constraints on validation

    For now, only zim_file name is not checked anymore. Typically used for youzim.it
    """

    zim_file = String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided).",
        },
        data_key="zim-file",
    )
