from marshmallow import fields, validate

from common.schemas import LongString, SerializableSchema, String, StringEnum
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
    validate_zim_longdescription,
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

    seeds = fields.Url(
        metadata={
            "label": "Seeds",
            "description": "The seed URL(s) to start crawling from. Multile seed URL "
            "must be separated by a comma (usually not needed, these are just the crawl"
            " seeds). First seed URL is used as ZIM homepage",
        },
    )

    seed_file = String(
        metadata={
            "label": "Seed File",
            "description": "If set, read a list of seed urls, one per line. HTTPS URL"
            " to an online file.",
        },
        data_key="seedFile",
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

    long_description = LongString(
        metadata={
            "label": "Long description",
            "description": "Optional long description for your ZIM",
        },
        validate=validate_zim_longdescription,
        data_key="long-description",
    )

    favicon = fields.Url(
        metadata={
            "label": "Illustration",
            "description": "URL for Illustration. "
            "If unspecified, will attempt to use favicon from main page.",
        },
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
    )

    wait_until = String(
        metadata={
            "label": "WaitUntil",
            "description": "Puppeteer page.goto() condition to wait for before "
            "continuing. One of load, domcontentloaded, networkidle0 or networkidle2, "
            "or a comma-separated combination of those. Default is load,networkidle2",
        },
        data_key="waitUntil",
    )

    depth = fields.Integer(
        metadata={
            "label": "Depth",
            "description": "The depth of the crawl for all seeds. Default is -1 "
            "(infinite).",
        },
    )

    extra_hops = fields.Integer(
        metadata={
            "label": "Extra Hops",
            "description": "Number of extra 'hops' to follow, "
            "beyond the current scope. Default is 0",
        },
        data_key="extraHops",
    )

    page_limit = fields.Integer(
        metadata={
            "label": "Page limit",
            "description": "Limit crawl to this number of pages. Default is 0 "
            "(no-limit).",
        },
        data_key="pageLimit",
    )

    max_page_limit = fields.Integer(
        metadata={
            "label": "Max Page Limit",
            "description": "Maximum pages to crawl, overriding pageLimit "
            "if both are set. Default is 0 (no-limit)",
        },
    )

    page_load_timeout = fields.Integer(
        metadata={
            "label": "Page Load Timeout",
            "description": "Timeout for each page to load (in seconds). Default is "
            "90 secs.",
        },
        data_key="pageLoadTimeout",
    )

    scope_type = StringEnum(
        metadata={
            "label": "Scope Type",
            "description": "A predfined scope of the crawl. For more customization, "
            "use 'custom' and set scopeIncludeRx/scopeExcludeRx regexes. Default is "
            "custom if scopeIncludeRx is set, prefix otherwise.",
        },
        data_key="scopeType",
        validate=validate.OneOf(
            ["page", "page-spa", "prefix", "host", "domain", "any", "custom"]
        ),
    )

    scope_include_rx = String(
        metadata={
            "label": "Scope Include Regex",
            "description": "Regex of page URLs that should be "
            "included in the crawl (defaults to the immediate directory of seed)",
        },
        data_key="scopeIncludeRx",
    )

    scope_exclude_rx = String(
        metadata={
            "label": "Scope Exclude Regex",
            "description": "Regex of page URLs that should be excluded from the crawl",
        },
        data_key="scopeExcludeRx",
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
    )

    mobile_device = StringEnum(
        metadata={
            "label": "As device",
            "description": "Device to crawl as. See Pupeeter's Device.ts for a list",
        },
        data_key="mobileDevice",
        validate=validate_devicelist,
    )

    select_links = String(
        metadata={
            "label": "Select Links",
            "description": "One or more selectors for extracting links, in the format "
            "[css selector]->[property to use],[css selector]->@[attribute to use]",
        },
        data_key="selectLinks",
    )

    click_selector = String(
        metadata={
            "label": "Click Selector",
            "description": "Selector for elements to click when using the autoclick "
            "behavior. Default is 'a'",
        },
        data_key="clickSelector",
    )

    block_rules = String(
        metadata={
            "label": "Block rules",
            "description": "Additional rules for blocking certain URLs from being "
            "loaded, by URL regex and optionally via text match in an iframe",
        },
        data_key="blockRules",
    )

    block_message = String(
        metadata={
            "label": "Block Message",
            "description": "If specified, when a URL is blocked, a record with this "
            "error message is added instead",
        },
        data_key="blockMessage",
    )

    block_ads = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Block Ads",
            "description": "If set, block advertisements from being loaded (based on "
            "Stephen Black's blocklist). Note that some bad domains are also blocked "
            "by zimit configuration even if this option is not set.",
        },
        data_key="blockAds",
    )

    ad_block_message = String(
        metadata={
            "label": "Ads Block Message",
            "description": "If specified, when an ad is blocked, a record with this "
            "error message is added instead",
        },
        data_key="adBlockMessage",
    )

    user_agent = String(
        metadata={
            "label": "User Agent",
            "description": "Override user-agent with specified",
        },
        data_key="userAgent",
    )

    user_agent_suffix = String(
        metadata={
            "label": "User Agent Suffix",
            "description": "Append suffix to existing browser user-agent. "
            "Defaults to +Zimit",
        },
        data_key="userAgentSuffix",
    )

    use_sitemap = fields.Url(
        metadata={
            "label": "Sitemap URL",
            "description": "Use as sitemap to get additional URLs for the crawl "
            "(usually at /sitemap.xml)",
        },
        data_key="useSitemap",
    )

    sitemap_from_date = fields.String(
        metadata={
            "label": "Sitemap From Date",
            "description": "If set, filter URLs from sitemaps to those greater than or "
            "equal to (>=) provided ISO Date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS "
            "or partial date)",
        },
        data_key="sitemapFromDate",
    )

    sitemap_to_date = fields.String(
        metadata={
            "label": "Sitemap To Date",
            "description": "If set, filter URLs from sitemaps to those less than or "
            "equal to (<=) provided ISO Date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS "
            "or partial date)",
        },
        data_key="sitemapToDate",
    )

    behaviors = String(
        metadata={
            "label": "Behaviors",
            "description": "Which background behaviors to enable on each page. "
            "Defaults to autoplay,autofetch,siteSpecific.",
        },
    )

    behavior_timeout = fields.Integer(
        metadata={
            "label": "Behavior Timeout",
            "description": "If >0, timeout (in seconds) for in-page behavior "
            "will run on each page. If 0, a behavior can run until finish. "
            "Default is 90.",
        },
        data_key="behaviorTimeout",
    )

    post_load_delay = fields.Integer(
        metadata={
            "label": "Post Load Delay",
            "description": "If >0, amount of time to sleep (in seconds) "
            "after page has loaded, before  taking screenshots / getting text / "
            "running behaviors. Default is 0.",
        },
        data_key="postLoadDelay",
    )

    page_extra_delay = fields.Integer(
        metadata={
            "label": "Page Extra Delay",
            "description": "If >0, amount of time to sleep (in seconds) "
            "after behaviors before moving on to next page. Default is 0.",
        },
        data_key="pageExtraDelay",
    )

    dedup_policy = fields.String(
        metadata={
            "label": "Dedup policy",
            "description": "Deduplication policy. Default is skip",
        },
        data_key="dedupPolicy",
        validate=validate.OneOf(["skip", "revisit", "keep"]),
    )

    screenshot = fields.String(
        metadata={
            "label": "Screenshot",
            "description": "Screenshot options for crawler. One of view, thumbnail, "
            "fullPage, fullPageFinal or a comma-separated combination of those.",
        },
    )

    size_soft_limit = fields.Integer(
        metadata={
            "label": "Size Soft Limit",
            "description": "If set, save crawl state and stop crawl if WARC size "
            "exceeds this value. ZIM will still be created.",
        },
        data_key="sizeSoftLimit",
    )

    size_hard_limit = fields.Integer(
        metadata={
            "label": "Size Hard Limit",
            "description": "If set, exit crawler and fail the scraper immediately if "
            "WARC size exceeds this value",
        },
        data_key="sizeHardLimit",
    )

    disk_utilization = fields.Integer(
        metadata={
            "label": "Disk Utilization",
            "description": "Save state and exit if disk utilization exceeds this "
            "percentage value. Default (if not set) is 90%. Set to 0 to disable disk "
            "utilization check.",
        },
        data_key="diskUtilization",
    )

    time_soft_limit = fields.Integer(
        metadata={
            "label": "Time Soft Limit",
            "description": "If set, save crawl state and stop crawl if WARC(s) "
            "creation takes longer than this value, in seconds. ZIM will still be "
            "created.",
        },
        data_key="timeSoftLimit",
    )

    time_hard_limit = fields.Integer(
        metadata={
            "label": "Time Hard Limit",
            "description": "If set, exit crawler and fail the scraper immediately if "
            "WARC(s) creation takes longer than this value, in seconds",
        },
        data_key="timeHardLimit",
    )

    net_idle_wait = fields.Integer(
        metadata={
            "label": "Net Idle Wait",
            "description": "If set, wait for network idle after page load and after "
            "behaviors are done (in seconds). If -1 (default), determine based on "
            "scope.",
        },
        data_key="netIdleWait",
    )

    origin_override = fields.String(
        metadata={
            "label": "Origin Override",
            "description": "If set, will redirect requests from each origin in key to "
            "origin in the value, eg. https://host:port=http://alt-host:alt-port.",
        },
        data_key="originOverride",
    )

    max_page_retries = fields.Integer(
        metadata={
            "label": "Max Page Retries",
            "description": "If set, number of times to retry a page that failed to load"
            " before page is considered to have failed. Default is 2.",
        },
        data_key="maxPageRetries",
    )

    fail_on_failed_seed = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Fail on failed seed",
            "description": "Whether to display additional logs",
        },
        data_key="failOnFailedSeed",
    )

    fail_on_invalid_status = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Fail on invalid status",
            "description": "If set, will treat pages with 4xx or 5xx response as "
            "failures. When combined with --failOnFailedLimit or --failOnFailedSeed "
            "may result in crawl failing due to non-200 responses",
        },
        data_key="failOnInvalidStatus",
    )

    fail_on_failed_limit = fields.Integer(
        metadata={
            "label": "Fail on failed - Limit",
            "description": "If set, save state and exit if number of failed pages "
            "exceeds this value.",
        },
        data_key="failOnFailedLimit",
    )

    custom_css = fields.Url(
        metadata={
            "label": "Custom CSS",
            "description": "URL to a CSS file to inject into pages",
        },
        data_key="custom-css",
    )

    verbose = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Verbose mode",
            "description": "Whether to display additional logs",
        },
    )

    keep = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Keep",
            "description": "Should be True. Developer option: must be True if we want "
            "to keep the WARC files for artifacts archiving.",
        },
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

    zimit_progress_file = String(
        metadata={
            "label": "Zimit progress file",
            "placeholder": "/output/task_progress.json",
            "description": "Scraping progress file. "
            "Leave it as `/output/task_progress.json`",
        },
        data_key="zimit-progress-file",
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
    )

    admin_email = String(
        metadata={
            "label": "Admin Email",
            "description": "Admin Email for crawler: used in UserAgent "
            "so website admin can contact us",
        },
        data_key="adminEmail",
    )

    charsets_to_try = String(
        metadata={
            "label": "Charsets to try",
            "description": "List of charsets to try decode content when charset is not "
            "defined at document or HTTP level. Single string, values separated by a "
            "comma. Default: UTF-8,ISO-8859-1",
        },
        data_key="charsets-to-try",
    )

    ignore_content_header_charsets = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Ignore Content Header Charsets",
            "description": "Ignore the charsets specified in content headers - first "
            "bytes - typically because they are wrong.",
        },
        data_key="ignore-content-header-charsets",
    )

    content_header_bytes_length = fields.Integer(
        metadata={
            "label": "Length of content header",
            "description": "How many bytes to consider when searching for content "
            "charsets in header (default is 1024).",
        },
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
        data_key="encoding-aliases",
    )

    profile = String(
        metadata={
            "label": "Browser profile",
            "description": "Path or HTTP(S) URL to tar.gz file which contains the "
            "browser profile directory for Browsertrix crawler.",
        },
    )

    custom_behaviors = String(
        metadata={
            "label": "Custom behaviors",
            "description": "JS code for custom behaviors to customize crawler. Single "
            "string with individual JS files URL/path separated by a comma.",
        },
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
