from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AnyUrl, Field, WrapValidator

from zimfarm_backend.common.schemas import CamelModel
from zimfarm_backend.common.schemas.fields import (
    OptionalField,
    OptionalNotEmptyString,
    OptionalPercentage,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    OptionalZIMProgressFile,
    OptionalZIMTitle,
    ZIMName,
    enum_member,
)


class ZimitScopeType(StrEnum):
    PAGE = "page"
    PAGE_SPA = "page-spa"
    PREFIX = "prefix"
    HOST = "host"
    DOMAIN = "domain"
    ANY = "any"
    CUSTOM = "custom"


ZimitScopeTypeValue = Annotated[
    ZimitScopeType, WrapValidator(enum_member(ZimitScopeType))
]


class ZimitDedupPolicy(StrEnum):
    SKIP = "skip"
    REVISIT = "revisit"
    KEEP = "keep"


ZimitDedupPolicyValue = Annotated[
    ZimitDedupPolicy, WrapValidator(enum_member(ZimitDedupPolicy))
]


# https://github.com/puppeteer/puppeteer/blob/main/src/common/DeviceDescriptors.ts
# https://github.com/puppeteer/puppeteer/blob/
# main/packages/puppeteer-core/src/common/Device.ts
class ZimitDevice(StrEnum):
    BLACKBERRY_PLAYBOOK = "Blackberry PlayBook"
    BLACKBERRY_PLAYBOOK_LANDSCAPE = "Blackberry PlayBook landscape"
    BLACKBERRY_Z30 = "BlackBerry Z30"
    BLACKBERRY_Z30_LANDSCAPE = "BlackBerry Z30 landscape"
    GALAXY_NOTE_3 = "Galaxy Note 3"
    GALAXY_NOTE_3_LANDSCAPE = "Galaxy Note 3 landscape"
    GALAXY_NOTE_II = "Galaxy Note II"
    GALAXY_NOTE_II_LANDSCAPE = "Galaxy Note II landscape"
    GALAXY_S_III = "Galaxy S III"
    GALAXY_S_III_LANDSCAPE = "Galaxy S III landscape"
    GALAXY_S5 = "Galaxy S5"
    GALAXY_S5_LANDSCAPE = "Galaxy S5 landscape"
    GALAXY_S8 = "Galaxy S8"
    GALAXY_S8_LANDSCAPE = "Galaxy S8 landscape"
    GALAXY_S9_PLUS = "Galaxy S9+"
    GALAXY_S9_PLUS_LANDSCAPE = "Galaxy S9+ landscape"
    GALAXY_TAB_S4 = "Galaxy Tab S4"
    GALAXY_TAB_S4_LANDSCAPE = "Galaxy Tab S4 landscape"
    IPAD = "iPad"
    IPAD_LANDSCAPE = "iPad landscape"
    IPAD_GEN_6 = "iPad (gen 6)"
    IPAD_GEN_6_LANDSCAPE = "iPad (gen 6) landscape"
    IPAD_GEN_7 = "iPad (gen 7)"
    IPAD_GEN_7_LANDSCAPE = "iPad (gen 7) landscape"
    IPAD_MINI = "iPad Mini"
    IPAD_MINI_LANDSCAPE = "iPad Mini landscape"
    IPAD_PRO = "iPad Pro"
    IPAD_PRO_LANDSCAPE = "iPad Pro landscape"
    IPAD_PRO_11 = "iPad Pro 11"
    IPAD_PRO_11_LANDSCAPE = "iPad Pro 11 landscape"
    IPHONE_4 = "iPhone 4"
    IPHONE_4_LANDSCAPE = "iPhone 4 landscape"
    IPHONE_5 = "iPhone 5"
    IPHONE_5_LANDSCAPE = "iPhone 5 landscape"
    IPHONE_6 = "iPhone 6"
    IPHONE_6_LANDSCAPE = "iPhone 6 landscape"
    IPHONE_6_PLUS = "iPhone 6 Plus"
    IPHONE_6_PLUS_LANDSCAPE = "iPhone 6 Plus landscape"
    IPHONE_7 = "iPhone 7"
    IPHONE_7_LANDSCAPE = "iPhone 7 landscape"
    IPHONE_7_PLUS = "iPhone 7 Plus"
    IPHONE_7_PLUS_LANDSCAPE = "iPhone 7 Plus landscape"
    IPHONE_8 = "iPhone 8"
    IPHONE_8_LANDSCAPE = "iPhone 8 landscape"
    IPHONE_8_PLUS = "iPhone 8 Plus"
    IPHONE_8_PLUS_LANDSCAPE = "iPhone 8 Plus landscape"
    IPHONE_SE = "iPhone SE"
    IPHONE_SE_LANDSCAPE = "iPhone SE landscape"
    IPHONE_X = "iPhone X"
    IPHONE_X_LANDSCAPE = "iPhone X landscape"
    IPHONE_XR = "iPhone XR"
    IPHONE_XR_LANDSCAPE = "iPhone XR landscape"
    IPHONE_11 = "iPhone 11"
    IPHONE_11_LANDSCAPE = "iPhone 11 landscape"
    IPHONE_11_PRO = "iPhone 11 Pro"
    IPHONE_11_PRO_LANDSCAPE = "iPhone 11 Pro landscape"
    IPHONE_11_PRO_MAX = "iPhone 11 Pro Max"
    IPHONE_11_PRO_MAX_LANDSCAPE = "iPhone 11 Pro Max landscape"
    IPHONE_12 = "iPhone 12"
    IPHONE_12_LANDSCAPE = "iPhone 12 landscape"
    IPHONE_12_PRO = "iPhone 12 Pro"
    IPHONE_12_PRO_LANDSCAPE = "iPhone 12 Pro landscape"
    IPHONE_12_PRO_MAX = "iPhone 12 Pro Max"
    IPHONE_12_PRO_MAX_LANDSCAPE = "iPhone 12 Pro Max landscape"
    IPHONE_12_MINI = "iPhone 12 Mini"
    IPHONE_12_MINI_LANDSCAPE = "iPhone 12 Mini landscape"
    IPHONE_13 = "iPhone 13"
    IPHONE_13_LANDSCAPE = "iPhone 13 landscape"
    IPHONE_13_PRO = "iPhone 13 Pro"
    IPHONE_13_PRO_LANDSCAPE = "iPhone 13 Pro landscape"
    IPHONE_13_PRO_MAX = "iPhone 13 Pro Max"
    IPHONE_13_PRO_MAX_LANDSCAPE = "iPhone 13 Pro Max landscape"
    IPHONE_13_MINI = "iPhone 13 Mini"
    IPHONE_13_MINI_LANDSCAPE = "iPhone 13 Mini landscape"
    JIO_PHONE_2 = "JioPhone 2"
    JIO_PHONE_2_LANDSCAPE = "JioPhone 2 landscape"
    KINDLE_FIRE_HDX = "Kindle Fire HDX"
    KINDLE_FIRE_HDX_LANDSCAPE = "Kindle Fire HDX landscape"
    LG_OPTIMUS_L70 = "LG Optimus L70"
    LG_OPTIMUS_L70_LANDSCAPE = "LG Optimus L70 landscape"
    MICROSOFT_LUMIA_550 = "Microsoft Lumia 550"
    MICROSOFT_LUMIA_950 = "Microsoft Lumia 950"
    MICROSOFT_LUMIA_950_LANDSCAPE = "Microsoft Lumia 950 landscape"
    NEXUS_10 = "Nexus 10"
    NEXUS_10_LANDSCAPE = "Nexus 10 landscape"
    NEXUS_4 = "Nexus 4"
    NEXUS_4_LANDSCAPE = "Nexus 4 landscape"
    NEXUS_5 = "Nexus 5"
    NEXUS_5_LANDSCAPE = "Nexus 5 landscape"
    NEXUS_5X = "Nexus 5X"
    NEXUS_5X_LANDSCAPE = "Nexus 5X landscape"
    NEXUS_6 = "Nexus 6"
    NEXUS_6_LANDSCAPE = "Nexus 6 landscape"
    NEXUS_6P = "Nexus 6P"
    NEXUS_6P_LANDSCAPE = "Nexus 6P landscape"
    NEXUS_7 = "Nexus 7"
    NEXUS_7_LANDSCAPE = "Nexus 7 landscape"
    NOKIA_LUMIA_520 = "Nokia Lumia 520"
    NOKIA_LUMIA_520_LANDSCAPE = "Nokia Lumia 520 landscape"
    NOKIA_N9 = "Nokia N9"
    NOKIA_N9_LANDSCAPE = "Nokia N9 landscape"
    PIXEL_2 = "Pixel 2"
    PIXEL_2_LANDSCAPE = "Pixel 2 landscape"
    PIXEL_2_XL = "Pixel 2 XL"
    PIXEL_2_XL_LANDSCAPE = "Pixel 2 XL landscape"
    PIXEL_3 = "Pixel 3"
    PIXEL_3_LANDSCAPE = "Pixel 3 landscape"
    PIXEL_4 = "Pixel 4"
    PIXEL_4_LANDSCAPE = "Pixel 4 landscape"
    PIXEL_4A_5G = "Pixel 4a (5G)"
    PIXEL_4A_5G_LANDSCAPE = "Pixel 4a (5G) landscape"
    PIXEL_5 = "Pixel 5"
    PIXEL_5_LANDSCAPE = "Pixel 5 landscape"
    MOTO_G4 = "Moto G4"
    MOTO_G4_LANDSCAPE = "Moto G4 landscape"


ZimitDeviceValue = Annotated[ZimitDevice, WrapValidator(enum_member(ZimitDevice))]


class ZimitFlagsFullSchema(CamelModel):
    seeds: OptionalNotEmptyString = OptionalField(
        title="Seeds",
        description="The seed URL(s) to start crawling from. Multile seed URL "
        "must be separated by a comma (usually not needed, these are just the crawl"
        " seeds). First seed URL is used as ZIM homepage",
    )
    seed_file: OptionalNotEmptyString = OptionalField(
        title="Seed File",
        description="If set, read a list of seed urls, one per line. HTTPS URL"
        " to an online file.",
    )
    name: ZIMName = Field(
        title="Name",
        description="Name of the ZIM. "
        "Used to compose filename if not otherwise defined",
    )
    lang: OptionalNotEmptyString = OptionalField(
        title="Browser Language",
        description="If set, sets the language used by the browser, should be"
        "ISO 639 language[-country] code, e.g. `en` or `en-GB`",
    )
    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for ZIM. Defaults to title of main page",
    )

    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Description for ZIM",
    )
    favicon: AnyUrl | None = OptionalField(
        title="Illustration",
        description="URL for Illustration. "
        "If unspecified, will attempt to use favicon from main page.",
    )
    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="Single string with individual tags separated by a semicolon.",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Content Creator",
        description="Name of content creator.",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). 'openZIM' otherwise",
    )

    source: OptionalNotEmptyString = OptionalField(
        title="Content Source",
        description="Source name/URL of content",
    )

    workers: int | None = OptionalField(
        title="Workers",
        description="The number of workers to run in parallel. Defaults to 1",
    )
    wait_until: OptionalNotEmptyString = OptionalField(
        title="WaitUntil",
        description="Puppeteer page.goto() condition to wait for before "
        "continuing. One of load, domcontentloaded, networkidle0 or networkidle2, "
        "or a comma-separated combination of those. Default is load,networkidle2",
    )

    extra_hops: int | None = OptionalField(
        title="Extra Hops",
        description="Number of extra 'hops' to follow, "
        "beyond the current scope. Default is 0",
    )

    page_limit: int | None = OptionalField(
        title="Page limit",
        description="Limit crawl to this number of pages. Default is 0 (no-limit).",
    )

    max_page_limit: int | None = OptionalField(
        title="Max Page Limit",
        description="Maximum pages to crawl, overriding pageLimit "
        "if both are set. Default is 0 (no-limit)",
    )

    page_load_timeout: int | None = OptionalField(
        title="Page Load Timeout",
        description="Timeout for each page to load (in seconds). Default is 90",
    )

    scope_type: ZimitScopeTypeValue | None = OptionalField(
        title="Scope Type",
        description="A predfined scope of the crawl. For more customization, "
        "use 'custom' and set scopeIncludeRx/scopeExcludeRx regexes. Default is "
        "custom if scopeIncludeRx is set, prefix otherwise.",
    )

    scope_include_rx: OptionalNotEmptyString = OptionalField(
        title="Scope Include Regex",
        description="Regex of page URLs that should be "
        "included in the crawl (defaults to the immediate directory of seed)",
    )

    scope_exclude_rx: OptionalNotEmptyString = OptionalField(
        title="Scope Exclude Regex",
        description="Regex of page URLs that should be excluded from the crawl",
    )

    allow_hash_urls: bool | None = OptionalField(
        title="Allow Hashtag URLs",
        description="Allow Hashtag URLs, useful for single-page-application "
        "crawling or when different hashtags load dynamic content",
    )

    mobile_device: ZimitDeviceValue | None = OptionalField(
        title="As device",
        description="Device to crawl as. See Pupeeter's Device.ts for a list",
    )

    select_links: OptionalNotEmptyString = OptionalField(
        title="Select Links",
        description="One or more selectors for extracting links, in the format "
        "[css selector]->[property to use],[css selector]->@[attribute to use]",
    )

    click_selector: OptionalNotEmptyString = OptionalField(
        title="Click Selector",
        description="Selector for elements to click when using the autoclick "
        "behavior. Default is 'a'",
    )

    block_rules: OptionalNotEmptyString = OptionalField(
        title="Block rules",
        description="Additional rules for blocking certain URLs from being "
        "loaded, by URL regex and optionally via text match in an iframe",
    )

    block_message: OptionalNotEmptyString = OptionalField(
        title="Block Message",
        description="If specified, when a URL is blocked, a record with this "
        "error message is added instead",
    )

    block_ads: bool | None = OptionalField(
        title="Block Ads",
        description="If set, block advertisements from being loaded (based on "
        "Stephen Black's blocklist). Note that some bad domains are also blocked "
        "by zimit configuration even if this option is not set.",
    )

    ad_block_message: OptionalNotEmptyString = OptionalField(
        title="Ads Block Message",
        description="If specified, when an ad is blocked, a record with this "
        "error message is added instead",
    )

    user_agent: OptionalNotEmptyString = OptionalField(
        title="User Agent",
        description="Override user-agent with specified",
    )

    user_agent_suffix: OptionalNotEmptyString = OptionalField(
        title="User Agent Suffix",
        description="Append suffix to existing browser user-agent. Defaults to +Zimit",
    )

    use_sitemap: OptionalNotEmptyString = OptionalField(
        title="Sitemap URL",
        description="Use as sitemap to get additional URLs for the crawl "
        "(usually at /sitemap.xml)",
    )

    sitemap_from_date: OptionalNotEmptyString = OptionalField(
        title="Sitemap From Date",
        description="If set, filter URLs from sitemaps to those greater than or "
        "equal to (>=) provided ISO Date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS "
        "or partial date)",
    )

    sitemap_to_date: OptionalNotEmptyString = OptionalField(
        title="Sitemap To Date",
        description="If set, filter URLs from sitemaps to those less than or "
        "equal to (<=) provided ISO Date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS "
        "or partial date)",
    )

    behavior_timeout: int | None = OptionalField(
        title="Behavior Timeout",
        description="If >0, timeout (in seconds) for in-page behavior "
        "will run on each page. If 0, a behavior can run until finish. "
        "Default is 90.",
    )

    post_load_delay: int | None = OptionalField(
        title="Post Load Delay",
        description="If >0, amount of time to sleep (in seconds) "
        "after page has loaded, before  taking screenshots / getting text / "
        "running behaviors. Default is 0.",
    )

    page_extra_delay: int | None = OptionalField(
        title="Page Extra Delay",
        description="If >0, amount of time to sleep (in seconds) "
        "after behaviors before moving on to next page. Default is 0.",
    )

    dedup_policy: ZimitDedupPolicyValue | None = OptionalField(
        title="Dedup policy",
        description="Deduplication policy. Default is skip",
    )

    screenshot: OptionalNotEmptyString = OptionalField(
        title="Screenshot",
        description="Screenshot options for crawler. One of view, thumbnail, "
        "fullPage, fullPageFinal or a comma-separated combination of those.",
    )

    size_soft_limit: int | None = OptionalField(
        title="Size Soft Limit",
        description="If set, save crawl state and stop crawl if WARC size "
        "exceeds this value. ZIM will still be created.",
    )

    size_hard_limit: int | None = OptionalField(
        title="Size Hard Limit",
        description="If set, exit crawler and fail the scraper immediately if "
        "WARC size exceeds this value",
    )

    disk_utilization: OptionalPercentage = OptionalField(
        title="Disk Utilization",
        description="Save state and exit if disk utilization exceeds this "
        "percentage value. Default (if not set) is 90%. Set to 0 to disable disk "
        "utilization check.",
    )

    time_soft_limit: int | None = OptionalField(
        title="Time Soft Limit",
        description="If set, save crawl state and stop crawl if WARC(s) "
        "creation takes longer than this value, in seconds. ZIM will still be "
        "created.",
    )

    time_hard_limit: int | None = OptionalField(
        title="Time Hard Limit",
        description="If set, exit crawler and fail the scraper immediately if "
        "WARC(s) creation takes longer than this value, in seconds",
    )

    net_idle_wait: int | None = OptionalField(
        title="Net Idle Wait",
        description="If set, wait for network idle after page load and after "
        "behaviors are done (in seconds). If -1 (default), determine based on "
        "scope.",
    )

    origin_override: OptionalNotEmptyString = OptionalField(
        title="Origin Override",
        description="If set, will redirect requests from each origin in key to "
        "origin in the value, eg. https://host:port=http://alt-host:alt-port.",
    )

    max_page_retries: int | None = OptionalField(
        title="Max Page Retries",
        description="If set, number of times to retry a page that failed to load"
        " before page is considered to have failed. Default is 2.",
    )

    fail_on_failed_seed: bool | None = OptionalField(
        title="Fail on failed seed",
        description="Whether to display additional logs",
    )

    fail_on_invalid_status: bool | None = OptionalField(
        title="Fail on invalid status",
        description="If set, will treat pages with 4xx or 5xx response as "
        "failures. When combined with --failOnFailedLimit or --failOnFailedSeed "
        "may result in crawl failing due to non-200 responses",
    )

    fail_on_failed_limit: int | None = OptionalField(
        title="Fail on failed - Limit",
        description="If set, save state and exit if number of failed pages "
        "exceeds this value.",
    )

    warcs: OptionalNotEmptyString = OptionalField(
        title="WARC files",
        description="Comma-separated list of WARC files to use as input.",
    )

    verbose: bool | None = OptionalField(
        title="Verbose mode",
        description="Whether to display additional logs",
    )

    keep: bool | None = OptionalField(
        title="Keep",
        description="Should be True. Developer option: must be True if we want "
        "to keep the WARC files for artifacts archiving.",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
    )

    admin_email: OptionalNotEmptyString = OptionalField(
        title="Admin Email",
        description="Admin Email for crawler: used in UserAgent "
        "so website admin can contact us",
        alias="adminEmail",
    )
    profile: OptionalNotEmptyString = OptionalField(
        title="Browser profile",
        description="Path or HTTP(S) URL to tar.gz file which contains the "
        "browser profile directory for Browsertrix crawler.",
    )

    behaviors: OptionalNotEmptyString = OptionalField(
        title="Behaviors",
        description="Which background behaviors to enable on each page. "
        "Defaults to autoplay,autofetch,siteSpecific.",
    )
    depth: int | None = OptionalField(
        title="Depth",
        description="The depth of the crawl for all seeds. Default is -1 (infinite).",
    )
    # Dash aliases
    zim_lang: OptionalNotEmptyString = OptionalField(
        title="ZIM Language",
        description="Language metadata of ZIM (warc2zim --lang param). "
        "ISO-639-3 code. Retrieved from homepage if found, fallback to `eng`",
        alias="zim-lang",
    )

    long_description: OptionalZIMLongDescription = OptionalField(
        title="Long description",
        description="Optional long description for your ZIM",
        alias="long-description",
    )

    custom_css: AnyUrl | None = OptionalField(
        title="Custom CSS",
        description="URL to a CSS file to inject into pages",
        alias="custom-css",
    )

    charsets_to_try: OptionalNotEmptyString = OptionalField(
        title="Charsets to try",
        description="List of charsets to try decode content when charset is not "
        "defined at document or HTTP level. Single string, values separated by a "
        "comma. Default: UTF-8,ISO-8859-1",
        alias="charsets-to-try",
    )

    ignore_content_header_charsets: bool | None = OptionalField(
        title="Ignore Content Header Charsets",
        description="Ignore the charsets specified in content headers - first "
        "bytes - typically because they are wrong.",
        alias="ignore-content-header-charsets",
    )

    content_header_bytes_length: int | None = OptionalField(
        title="Length of content header",
        description="How many bytes to consider when searching for content "
        "charsets in header (default is 1024).",
        alias="content-header-bytes-length",
    )

    ignore_http_header_charsets: bool | None = OptionalField(
        title="Ignore HTTP Header Charsets",
        description="Ignore the charsets specified in HTTP `Content-Type` "
        "headers, typically because they are wrong.",
        alias="ignore-http-header-charsets",
    )

    encoding_aliases: OptionalNotEmptyString = OptionalField(
        title="Encoding aliases",
        description="List of encoding/charset aliases to decode WARC content. "
        "Aliases are used when the encoding specified in upstream server exists in"
        " Python under a different name. This parameter has the format "
        "alias_encoding=python_encoding. This parameter is single string, multiple"
        " values are separated by a comma, like in "
        "alias1=encoding1,alias2=encoding2.",
        alias="encoding-aliases",
    )

    custom_behaviors: OptionalNotEmptyString = OptionalField(
        title="Custom behaviors",
        description="JS code for custom behaviors to customize crawler. Single "
        "string with individual JS files URL/path separated by a comma.",
        alias="custom-behaviours",
    )

    zimit_progress_file: OptionalZIMProgressFile = OptionalField(
        title="Zimit progress file",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
        alias="zimit-progress-file",
    )

    replay_viewer_source: AnyUrl | None = OptionalField(
        title="Replay Viewer Source",
        description="URL from which to load the ReplayWeb.page replay viewer from",
        alias="replay-viewer-source",
    )


class ZimitFlagsSchema(ZimitFlagsFullSchema):
    offliner_id: Literal["zimit"] = Field(alias="offliner_id")
    zim_file: OptionalZIMFileName = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Make sure to end with _{period}.zim",
        alias="zim-file",
    )


class ZimitFlagsSchemaRelaxed(ZimitFlagsFullSchema):
    """A Zimit flags schema with relaxed constraints on validation

    For now, only zim_file name is not checked anymore. Typically used for youzim.it
    """

    offliner_id: Literal["zimit"] = Field(alias="offliner_id")
    zim_file: OptionalNotEmptyString = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided).",
        alias="zim-file",
    )
