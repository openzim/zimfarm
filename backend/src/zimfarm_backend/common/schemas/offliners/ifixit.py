from pydantic import Field
from pydantic.types import AnyUrl

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    Percentage,
    S3OptimizationCache,
    ZIMDescription,
    ZIMFileName,
    ZIMOutputFolder,
    ZIMTitle,
)


class IFixitFlagsSchema(BaseModel):
    language: NotEmptyString = Field(
        title="Language",
        description="iFixIt website to build from",
    )

    name: NotEmptyString = Field(
        title="Name",
        description="ZIM name. Used as identifier and filename "
        "(date will be appended). Constructed from language if not supplied",
    )

    title: ZIMTitle = Field(
        title="Title",
        description="Custom title for your ZIM. iFixIt homepage title otherwise",
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Custom description for your ZIM. "
        "iFixIt homepage description (meta) otherwise",
    )

    icon: AnyUrl | None = Field(
        title="Icon",
        description="Custom Icon for your ZIM (URL). iFixit square logo otherwise",
        default=None,
    )

    creator: NotEmptyString = Field(
        title="Creator",
        description="Name of content creator. “iFixit” otherwise",
        default="iFixit",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description="List of semi-colon-separated Tags for the ZIM file. "
        "_category:ifixit and ifixit added automatically",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
        default="/output",
        validate_default=True,
    )

    tmp_dir: ZIMOutputFolder = Field(
        title="Temp folder",
        description="Where to create temporay build folder. Leave it as `/output`",
        default="/output",
        alias="tmp-dir",
        validate_default=True,
    )

    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Include {period} to insert date period dynamically",
        alias="zim-file",
    )

    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
        alias="optimization-cache",
    )

    stats_filename: NotEmptyString = Field(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
        default="/output/task_progress.json",
        alias="stats-filename",
        pattern=r"^/output/task_progress\.json$",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )

    delay: float = Field(
        title="Delay",
        description="Add this delay (seconds) "
        "before each request to please iFixit servers. Can be fractions. "
        "Defaults to 0: no delay",
        default=0,
    )

    api_delay: float = Field(
        title="API Delay",
        description="Add this delay (seconds) "
        "before each API query (!= calls) to please iFixit servers. "
        "Can be fractions. Defaults to 0: no delay",
        alias="api-delay",
        default=0,
    )

    cdn_delay: float = Field(
        title="CDN Delay",
        description="Add this delay (seconds) "
        "before each CDN file download to please iFixit servers. "
        "Can be fractions. Defaults to 0: no delay",
        alias="cdn-delay",
        default=0,
    )

    max_missing_items: Percentage = Field(
        title="Max Missing Items",
        description="Amount of missing items which will force the scraper to "
        "stop, expressed as a percentage of the total number of items to retrieve. "
        "Integer from 1 to 100",
        alias="max-missing-items-percent",
    )

    max_error_items: Percentage = Field(
        title="Max Error Items",
        description="Amount of items with failed processing which will force "
        "the scraper to stop, expressed as a percentage of the total number of "
        "items to retrieve. Integer from 1 to 100",
        alias="max-error-items-percent",
    )

    categories: NotEmptyString = Field(
        title="Categories",
        description="Only scrape those categories (comma-separated). "
        "Specify the category names",
    )

    no_category: bool = Field(
        title="No category",
        description="Do not scrape any category",
        alias="no-category",
    )

    guide: NotEmptyString = Field(
        title="Guides",
        description="Only scrape this guide (comma-separated)). "
        "Specify the guide names",
    )

    no_guide: bool = Field(
        title="No guide",
        description="Do not scrape any guide",
        alias="no-guide",
    )

    info: NotEmptyString = Field(
        title="Info",
        description="Only scrape this info (comma-separated)). Specify the info names",
    )

    no_info: bool = Field(
        title="No info",
        description="Do not scrape any info",
        alias="no-info",
    )
