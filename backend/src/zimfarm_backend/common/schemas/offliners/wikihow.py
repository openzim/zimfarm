from typing import Literal

from pydantic import AnyUrl, Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    OptionalNotEmptyString,
    OptionalS3OptimizationCache,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMOutputFolder,
    OptionalZIMProgressFile,
    OptionalZIMTitle,
)


class WikihowFlagsSchema(DashModel):
    offliner_id: Literal["wikihow"] = Field(exclude=True)

    language: NotEmptyString = Field(
        title="Language",
        description="wikiHow website to build from. 2-letters language code.",
    )

    name: OptionalNotEmptyString = OptionalField(
        title="Name",
        description="ZIM name. Used as identifier and filename "
        "(date will be appended). Constructed from language if not supplied",
    )

    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for your ZIM. Wikihow homepage title otherwise",
    )

    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Custom description for your ZIM. "
        "Wikihow homepage description (meta) otherwise",
    )

    icon: AnyUrl | None = OptionalField(
        title="Icon",
        description="Custom Icon for your ZIM (URL). wikiHow square logo otherwise",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Creator",
        description='Name of content creator. "wikiHow" otherwise',
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description='Custom publisher name (ZIM metadata). "openZIM" otherwise',
    )

    tag: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="List of semi-colon-separated Tags for the ZIM file. "
        "_category:other and wikihow added automatically",
    )

    without_external_links: bool | None = OptionalField(
        title="Without External links",
        description="Remove all external links from pages. "
        "Link text is kept but not the address",
    )

    without_videos: bool | None = OptionalField(
        title="Without Videos",
        description="Don't include the video blocks (Youtube hosted). "
        "Most are copyrighted",
    )

    exclude: AnyUrl | None = OptionalField(
        title="Exclude",
        description="URL to a text file listing Article ID or "
        "`Category:` prefixed Category IDs to exclude from the scrape. "
        "Lines starting with # are ignored",
    )

    only: AnyUrl | None = OptionalField(
        title="Only",
        description="URL to a text file listing Article IDs. "
        "This filters out every other article. "
        "Lines starting with # are ignored",
    )

    low_quality: bool | None = OptionalField(
        title="Low quality",
        description="Use lower-quality, smaller file-size video encode",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
    )

    tmp_dir: OptionalZIMOutputFolder = OptionalField(
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

    categories: OptionalNotEmptyString = OptionalField(
        title="Categories",
        description="Only scrape those categories (comma-separated). "
        "Use URL-ID of the Category "
        "(after the colon `:` in the URL). "
        "Add a slash after Category to request it without recursion",
    )

    stats_filename: OptionalZIMProgressFile = OptionalField(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )

    missing_article_tolerance: int | None = OptionalField(
        title="Missing tolerance",
        description="Allow this percentage (0-100) of articles to "
        "be missing (HTTP 404). Defaults to 0: no tolerance",
        ge=0,
        le=100,
    )

    delay: float | None = OptionalField(
        title="Delay",
        description="Add this delay (seconds) "
        "before each request to please wikiHow servers. Can be fractions. "
        "Defaults to 0: no delay",
    )

    api_delay: float | None = OptionalField(
        title="API Delay",
        description="Add this delay (seconds) "
        "before each API query (!= calls) to please wikiHow servers. "
        "Can be fractions. Defaults to 0: no delay",
    )
