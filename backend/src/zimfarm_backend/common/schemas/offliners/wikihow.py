from pydantic import Field
from pydantic.types import AnyUrl

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    S3OptimizationCache,
    ZIMDescription,
    ZIMFileName,
    ZIMOutputFolder,
    ZIMTitle,
)


class WikihowFlagsSchema(BaseModel):
    language: NotEmptyString = Field(
        title="Language",
        description="wikiHow website to build from. 2-letters language code.",
    )

    name: NotEmptyString | None = Field(
        title="Name",
        description="ZIM name. Used as identifier and filename "
        "(date will be appended). Constructed from language if not supplied",
        default=None,
    )

    title: ZIMTitle = Field(
        title="Title",
        description="Custom title for your ZIM. Wikihow homepage title otherwise",
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Custom description for your ZIM. "
        "Wikihow homepage description (meta) otherwise",
    )

    icon: AnyUrl | None = Field(
        title="Icon",
        description="Custom Icon for your ZIM (URL). wikiHow square logo otherwise",
        default=None,
    )

    creator: NotEmptyString = Field(
        title="Creator",
        description="Name of content creator. “wikiHow” otherwise",
        default="wikiHow",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    tag: NotEmptyString = Field(
        title="ZIM Tags",
        description="List of semi-colon-separated Tags for the ZIM file. "
        "_category:other and wikihow added automatically",
    )

    without_external_links: bool = Field(
        title="Without External links",
        description="Remove all external links from pages. "
        "Link text is kept but not the address",
        alias="without-external-links",
    )

    without_videos: bool = Field(
        title="Without Videos",
        description="Don't include the video blocks (Youtube hosted). "
        "Most are copyrighted",
        alias="without-videos",
    )

    exclude: AnyUrl = Field(
        title="Exclude",
        description="URL to a text file listing Article ID or "
        "`Category:` prefixed Category IDs to exclude from the scrape. "
        "Lines starting with # are ignored",
    )

    only: AnyUrl = Field(
        title="Only",
        description="URL to a text file listing Article IDs. "
        "This filters out every other article. "
        "Lines starting with # are ignored",
    )

    low_quality: bool = Field(
        title="Low quality",
        description="Use lower-quality, smaller file-size video encode",
        alias="low-quality",
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
        validate_default=True,
        alias="tmp-dir",
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

    categories: NotEmptyString = Field(
        title="Categories",
        description="Only scrape those categories (comma-separated). "
        "Use URL-ID of the Category "
        "(after the colon `:` in the URL). "
        "Add a slash after Category to request it without recursion",
    )

    stats_filename: NotEmptyString = Field(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
        default="/output/task_progress.json",
        validate_default=True,
        alias="stats-filename",
        pattern=r"^/output/task_progress\.json$",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )

    missing_article_tolerance: int = Field(
        title="Missing tolerance",
        description="Allow this percentage (0-100) of articles to "
        "be missing (HTTP 404). Defaults to 0: no tolerance",
        alias="missing-article-tolerance",
        ge=0,
        le=100,
    )

    delay: float = Field(
        title="Delay",
        description="Add this delay (seconds) "
        "before each request to please wikiHow servers. Can be fractions. "
        "Defaults to 0: no delay",
        default=0,
    )

    api_delay: float = Field(
        title="API Delay",
        description="Add this delay (seconds) "
        "before each API query (!= calls) to please wikiHow servers. "
        "Can be fractions. Defaults to 0: no delay",
        alias="api-delay",
        default=0,
    )
