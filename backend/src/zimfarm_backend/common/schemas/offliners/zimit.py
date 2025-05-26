from typing import Literal

from pydantic import Field, field_validator
from pydantic.types import AnyUrl

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    Percentage,
    ZIMDescription,
    ZIMFileName,
    ZIMLongDescription,
    ZIMOutputFolder,
    ZIMTitle,
)

# https://github.com/puppeteer/puppeteer/blob/main/src/common/DeviceDescriptors.ts
# https://github.com/puppeteer/puppeteer/blob/
# main/packages/puppeteer-core/src/common/Device.ts
DEVICES = sorted(
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


class ZimitFlagsSchema(BaseModel):
    seeds: AnyUrl = Field(
        title="Seeds",
        description="The seed URL(s) to start crawling from. Multile seed URL "
        "must be separated by a comma (usually not needed, these are just the crawl"
        " seeds). First seed URL is used as ZIM homepage",
    )

    seed_file: AnyUrl = Field(
        title="Seed File",
        description="If set, read a list of seed urls, one per line. HTTPS URL"
        " to an online file.",
        alias="seed-file",
    )

    name: NotEmptyString = Field(
        title="Name",
        description="Name of the ZIM. "
        "Used to compose filename if not otherwise defined",
    )

    lang: NotEmptyString = Field(
        title="Browser Language",
        description="If set, sets the language used by the browser, should be"
        "ISO 639 language[-country] code, e.g. `en` or `en-GB`",
    )

    zim_lang: NotEmptyString = Field(
        title="ZIM Language",
        description="Language metadata of ZIM (warc2zim --lang param). "
        "ISO-639-3 code. Retrieved from homepage if found, fallback to `eng`",
        alias="zim-lang",
    )

    title: ZIMTitle = Field(
        title="Title",
        description="Custom title for ZIM. Defaults to title of main page",
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Description for ZIM",
    )

    long_description: ZIMLongDescription = Field(
        title="Long description",
        description="Optional long description for your ZIM",
        alias="long-description",
    )

    favicon: AnyUrl | None = Field(
        title="Illustration",
        default=None,
        description="URL for Illustration. "
        "If unspecified, will attempt to use favicon from main page.",
    )

    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Make sure to end with _{period}.zim",
        alias="zim-file",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description="Single string with individual tags separated by a semicolon.",
    )

    creator: NotEmptyString = Field(
        title="Content Creator",
        description="Name of content creator.",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    source: NotEmptyString = Field(
        title="Content Source",
        description="Source name/URL of content",
    )

    workers: int = Field(
        title="Workers",
        description="The number of workers to run in parallel. Defaults to 1",
        default=1,
    )

    wait_until: NotEmptyString = Field(
        title="WaitUntil",
        description="Puppeteer page.goto() condition to wait for before "
        "continuing. One of load, domcontentloaded, networkidle0 or networkidle2, "
        "or a comma-separated combination of those. Default is load,networkidle2",
        default="load,networkidle2",
        alias="waitUntil",
    )

    depth: int = Field(
        title="Depth",
        description="The depth of the crawl for all seeds. Default is -1 (infinite).",
        default=-1,
    )

    extra_hops: int = Field(
        title="Extra Hops",
        description="Number of extra 'hops' to follow, "
        "beyond the current scope. Default is 0",
        default=0,
        alias="extraHops",
    )

    page_limit: int = Field(
        title="Page limit",
        description="Limit crawl to this number of pages. Default is 0 (no-limit).",
        default=0,
        alias="pageLimit",
    )

    max_page_limit: int = Field(
        title="Max Page Limit",
        description="Maximum pages to crawl, overriding pageLimit "
        "if both are set. Default is 0 (no-limit)",
        default=0,
        alias="maxPageLimit",
    )

    page_load_timeout: int = Field(
        title="Page Load Timeout",
        description="Timeout for each page to load (in seconds). Default is 90",
        default=90,
        alias="pageLoadTimeout",
    )

    scope_type: Literal[
        "page", "page-spa", "prefix", "host", "domain", "any", "custom"
    ] = Field(
        title="Scope Type",
        description="A predfined scope of the crawl. For more customization, "
        "use 'custom' and set scopeIncludeRx/scopeExcludeRx regexes. Default is "
        "custom if scopeIncludeRx is set, prefix otherwise.",
        default="custom",
        alias="scopeType",
    )

    scope_include_rx: NotEmptyString | None = Field(
        title="Scope Include Regex",
        description="Regex of page URLs that should be "
        "included in the crawl (defaults to the immediate directory of seed)",
        alias="scopeIncludeRx",
    )

    scope_exclude_rx: NotEmptyString = Field(
        title="Scope Exclude Regex",
        description="Regex of page URLs that should be excluded from the crawl",
        alias="scopeExcludeRx",
    )

    allow_hash_urls: bool = Field(
        title="Allow Hashtag URLs",
        description="Allow Hashtag URLs, useful for single-page-application "
        "crawling or when different hashtags load dynamic content",
        alias="allowHashUrls",
    )

    mobile_device: NotEmptyString = Field(
        title="As device",
        description="Device to crawl as. See Pupeeter's Device.ts for a list",
        alias="mobileDevice",
    )

    @field_validator("mobile_device")
    def validate_mobile_device(cls, v: NotEmptyString):  # noqa: N805
        if v not in DEVICES:
            raise ValueError(f"Invalid device: {v}")
        return v

    select_links: NotEmptyString = Field(
        title="Select Links",
        description="One or more selectors for extracting links, in the format "
        "[css selector]->[property to use],[css selector]->@[attribute to use]",
        alias="selectLinks",
    )

    click_selector: NotEmptyString = Field(
        title="Click Selector",
        description="Selector for elements to click when using the autoclick "
        "behavior. Default is 'a'",
        alias="clickSelector",
        default="a",
    )

    block_rules: NotEmptyString = Field(
        title="Block rules",
        description="Additional rules for blocking certain URLs from being "
        "loaded, by URL regex and optionally via text match in an iframe",
        alias="blockRules",
    )

    block_message: NotEmptyString | None = Field(
        title="Block Message",
        description="If specified, when a URL is blocked, a record with this "
        "error message is added instead",
        alias="blockMessage",
    )

    block_ads: bool = Field(
        title="Block Ads",
        description="If set, block advertisements from being loaded (based on "
        "Stephen Black's blocklist). Note that some bad domains are also blocked "
        "by zimit configuration even if this option is not set.",
        alias="blockAds",
    )

    ad_block_message: NotEmptyString | None = Field(
        title="Ads Block Message",
        description="If specified, when an ad is blocked, a record with this "
        "error message is added instead",
        alias="adBlockMessage",
    )

    user_agent: NotEmptyString | None = Field(
        title="User Agent",
        description="Override user-agent with specified",
        alias="userAgent",
    )

    user_agent_suffix: NotEmptyString = Field(
        title="User Agent Suffix",
        description="Append suffix to existing browser user-agent. Defaults to +Zimit",
        alias="userAgentSuffix",
        default="+Zimit",
    )

    use_sitemap: AnyUrl = Field(
        title="Sitemap URL",
        description="Use as sitemap to get additional URLs for the crawl "
        "(usually at /sitemap.xml)",
        alias="useSitemap",
    )

    sitemap_from_date: NotEmptyString | None = Field(
        title="Sitemap From Date",
        description="If set, filter URLs from sitemaps to those greater than or "
        "equal to (>=) provided ISO Date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS "
        "or partial date)",
        alias="sitemapFromDate",
        default=None,
    )

    sitemap_to_date: NotEmptyString | None = Field(
        title="Sitemap To Date",
        description="If set, filter URLs from sitemaps to those less than or "
        "equal to (<=) provided ISO Date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS "
        "or partial date)",
        alias="sitemapToDate",
        default=None,
    )

    behaviors: NotEmptyString = Field(
        title="Behaviors",
        description="Which background behaviors to enable on each page. "
        "Defaults to autoplay,autofetch,siteSpecific.",
        default="autoplay,autofetch,siteSpecific",
    )

    behavior_timeout: int = Field(
        title="Behavior Timeout",
        description="If >0, timeout (in seconds) for in-page behavior "
        "will run on each page. If 0, a behavior can run until finish. "
        "Default is 90.",
        default=90,
        alias="behaviorTimeout",
    )

    post_load_delay: int = Field(
        title="Post Load Delay",
        description="If >0, amount of time to sleep (in seconds) "
        "after page has loaded, before  taking screenshots / getting text / "
        "running behaviors. Default is 0.",
        default=0,
        alias="postLoadDelay",
    )

    page_extra_delay: int = Field(
        title="Page Extra Delay",
        description="If >0, amount of time to sleep (in seconds) "
        "after behaviors before moving on to next page. Default is 0.",
        default=0,
        alias="pageExtraDelay",
    )

    dedup_policy: Literal["skip", "revisit", "keep"] = Field(
        title="Dedup policy",
        description="Deduplication policy. Default is skip",
        default="skip",
        alias="dedupPolicy",
    )

    screenshot: NotEmptyString = Field(
        title="Screenshot",
        description="Screenshot options for crawler. One of view, thumbnail, "
        "fullPage, fullPageFinal or a comma-separated combination of those.",
        alias="screenshot",
    )

    size_soft_limit: int = Field(
        title="Size Soft Limit",
        description="If set, save crawl state and stop crawl if WARC size "
        "exceeds this value. ZIM will still be created.",
        default=0,
        alias="sizeSoftLimit",
    )

    size_hard_limit: int = Field(
        title="Size Hard Limit",
        description="If set, exit crawler and fail the scraper immediately if "
        "WARC size exceeds this value",
        default=0,
        alias="sizeHardLimit",
    )

    disk_utilization: Percentage = Field(
        title="Disk Utilization",
        description="Save state and exit if disk utilization exceeds this "
        "percentage value. Default (if not set) is 90%. Set to 0 to disable disk "
        "utilization check.",
        default=90,
        alias="diskUtilization",
    )

    time_soft_limit: int = Field(
        title="Time Soft Limit",
        description="If set, save crawl state and stop crawl if WARC(s) "
        "creation takes longer than this value, in seconds. ZIM will still be "
        "created.",
        default=0,
        alias="timeSoftLimit",
    )

    time_hard_limit: int = Field(
        title="Time Hard Limit",
        description="If set, exit crawler and fail the scraper immediately if "
        "WARC(s) creation takes longer than this value, in seconds",
        default=0,
        alias="timeHardLimit",
    )

    net_idle_wait: int = Field(
        title="Net Idle Wait",
        description="If set, wait for network idle after page load and after "
        "behaviors are done (in seconds). If -1 (default), determine based on "
        "scope.",
        default=-1,
        alias="netIdleWait",
    )

    origin_override: NotEmptyString | None = Field(
        title="Origin Override",
        description="If set, will redirect requests from each origin in key to "
        "origin in the value, eg. https://host:port=http://alt-host:alt-port.",
        alias="originOverride",
    )

    max_page_retries: int = Field(
        title="Max Page Retries",
        description="If set, number of times to retry a page that failed to load"
        " before page is considered to have failed. Default is 2.",
        default=2,
        alias="maxPageRetries",
    )

    fail_on_failed_seed: bool = Field(
        title="Fail on failed seed",
        description="Whether to display additional logs",
        alias="failOnFailedSeed",
    )

    fail_on_invalid_status: bool = Field(
        title="Fail on invalid status",
        description="If set, will treat pages with 4xx or 5xx response as "
        "failures. When combined with --failOnFailedLimit or --failOnFailedSeed "
        "may result in crawl failing due to non-200 responses",
        alias="failOnInvalidStatus",
    )

    fail_on_failed_limit: int = Field(
        title="Fail on failed - Limit",
        description="If set, save state and exit if number of failed pages "
        "exceeds this value.",
        default=0,
        alias="failOnFailedLimit",
    )

    custom_css: AnyUrl = Field(
        title="Custom CSS",
        description="URL to a CSS file to inject into pages",
        alias="custom-css",
    )

    verbose: bool = Field(
        title="Verbose mode",
        description="Whether to display additional logs",
    )

    keep: bool = Field(
        title="Keep",
        description="Should be True. Developer option: must be True if we want "
        "to keep the WARC files for artifacts archiving.",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
        default="/output",
    )

    zimit_progress_file: NotEmptyString = Field(
        title="Zimit progress file",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
        default="/output/task_progress.json",
        pattern=r"^/output/task_progress\.json$",
    )

    replay_viewer_source: AnyUrl = Field(
        title="Replay Viewer Source",
        description="URL from which to load the ReplayWeb.page replay viewer from",
        alias="replay-viewer-source",
    )

    admin_email: NotEmptyString = Field(
        title="Admin Email",
        description="Admin Email for crawler: used in UserAgent "
        "so website admin can contact us",
        alias="adminEmail",
    )

    charsets_to_try: NotEmptyString = Field(
        title="Charsets to try",
        description="List of charsets to try decode content when charset is not "
        "defined at document or HTTP level. Single string, values separated by a "
        "comma. Default: UTF-8,ISO-8859-1",
        alias="charsets-to-try",
    )

    ignore_content_header_charsets: bool = Field(
        title="Ignore Content Header Charsets",
        description="Ignore the charsets specified in content headers - first "
        "bytes - typically because they are wrong.",
        alias="ignore-content-header-charsets",
    )

    content_header_bytes_length: int = Field(
        title="Length of content header",
        description="How many bytes to consider when searching for content "
        "charsets in header (default is 1024).",
        alias="content-header-bytes-length",
        default=1024,
    )

    ignore_http_header_charsets: bool = Field(
        title="Ignore HTTP Header Charsets",
        description="Ignore the charsets specified in HTTP `Content-Type` "
        "headers, typically because they are wrong.",
        alias="ignore-http-header-charsets",
    )

    encoding_aliases: NotEmptyString = Field(
        title="Encoding aliases",
        description="List of encoding/charset aliases to decode WARC content. "
        "Aliases are used when the encoding specified in upstream server exists in"
        " Python under a different name. This parameter has the format "
        "alias_encoding=python_encoding. This parameter is single string, multiple"
        " values are separated by a comma, like in "
        "alias1=encoding1,alias2=encoding2.",
        alias="encoding-aliases",
    )

    profile: NotEmptyString = Field(
        title="Browser profile",
        description="Path or HTTP(S) URL to tar.gz file which contains the "
        "browser profile directory for Browsertrix crawler.",
        alias="profile",
    )

    custom_behaviors: NotEmptyString = Field(
        title="Custom behaviors",
        description="JS code for custom behaviors to customize crawler. Single "
        "string with individual JS files URL/path separated by a comma.",
        alias="custom-behaviors",
    )

    warcs: NotEmptyString = Field(
        title="WARC files",
        description="Directly convert WARC archives to ZIM, by-passing the "
        "crawling phase. This argument must contain the path or HTTP(S) URL to "
        "either warc.gz files or to a tar.gz containing the warc.gz files. "
        "Single value with individual path/URLs separated by comma.",
        alias="warcs",
    )


class ZimitFlagsSchemaRelaxed(ZimitFlagsSchema):
    """A Zimit flags schema with relaxed constraints on validation

    For now, only zim_file name is not checked anymore. Typically used for youzim.it
    """

    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided).",
        alias="zim-file",
    )
