from pydantic import AnyUrl, Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    OptionalNotEmptyString,
    OptionalPercentage,
    OptionalS3OptimizationCache,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMOutputFolder,
    OptionalZIMProgressFile,
    OptionalZIMTitle,
)


class IFixitFlagsSchema(DashModel):
    language: NotEmptyString = Field(
        title="Language",
        description="iFixIt website to build from",
    )

    name: OptionalNotEmptyString = OptionalField(
        title="Name",
        description="ZIM name. Used as identifier and filename "
        "(date will be appended). Constructed from language if not supplied",
    )

    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for your ZIM. iFixIt homepage title otherwise",
    )

    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Custom description for your ZIM. "
        "iFixIt homepage description (meta) otherwise",
    )

    icon: AnyUrl | None = OptionalField(
        title="Icon",
        description="Custom Icon for your ZIM (URL). iFixit square logo otherwise",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Creator",
        description="Name of content creator. “iFixit” otherwise",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). openZIM otherwise",
    )

    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="List of semi-colon-separated Tags for the ZIM file. "
        "_category:ifixit and ifixit added automatically",
    )

    output: OptionalZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
    )

    tmp_dir: OptionalZIMOutputFolder = Field(
        title="Temp folder",
        description="Where to create temporay build folder. Leave it as `/output`",
    )

    zim_file: OptionalZIMFileName = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Include {period} to insert date period dynamically",
    )

    optimization_cache: OptionalS3OptimizationCache = OptionalField(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
    )

    stats_filename: OptionalZIMProgressFile = OptionalField(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )

    delay: float | None = OptionalField(
        title="Delay",
        description="Add this delay (seconds) "
        "before each request to please iFixit servers. Can be fractions. "
        "Defaults to 0: no delay",
    )

    api_delay: float | None = OptionalField(
        title="API Delay",
        description="Add this delay (seconds) "
        "before each API query (!= calls) to please iFixit servers. "
        "Can be fractions. Defaults to 0: no delay",
    )

    cdn_delay: float | None = OptionalField(
        title="CDN Delay",
        description="Add this delay (seconds) "
        "before each CDN file download to please iFixit servers. "
        "Can be fractions. Defaults to 0: no delay",
    )

    max_missing_items: OptionalPercentage = OptionalField(
        title="Max Missing Items",
        description="Amount of missing items which will force the scraper to "
        "stop, expressed as a percentage of the total number of items to retrieve. "
        "Integer from 1 to 100",
    )

    max_error_items: OptionalPercentage = OptionalField(
        title="Max Error Items",
        description="Amount of items with failed processing which will force "
        "the scraper to stop, expressed as a percentage of the total number of "
        "items to retrieve. Integer from 1 to 100",
    )

    categories: OptionalNotEmptyString = OptionalField(
        title="Categories",
        description="Only scrape those categories (comma-separated). "
        "Specify the category names",
    )

    no_category: bool | None = OptionalField(
        title="No category",
        description="Do not scrape any category",
    )

    guide: OptionalNotEmptyString = OptionalField(
        title="Guides",
        description="Only scrape this guide (comma-separated)). "
        "Specify the guide names",
    )

    no_guide: bool | None = OptionalField(
        title="No guide",
        description="Do not scrape any guide",
    )

    info: OptionalNotEmptyString = OptionalField(
        title="Info",
        description="Only scrape this info (comma-separated)). Specify the info names",
    )

    no_info: bool | None = OptionalField(
        title="No info",
        description="Do not scrape any info",
    )
