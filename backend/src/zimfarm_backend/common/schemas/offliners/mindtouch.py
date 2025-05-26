from pydantic import Field
from pydantic.types import AnyUrl

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    S3OptimizationCache,
    ZIMDescription,
    ZIMLongDescription,
    ZIMOutputFolder,
    ZIMTitle,
)


class MindtouchFlagsSchema(BaseModel):
    library_url: NotEmptyString = Field(
        title="Library URL",
        description="URL of the Mindtouch / Nice CXone Expert instance (must NOT"
        " contain trailing slash), e.g. for LibreTexts Geosciences it is "
        "https://geo.libretexts.org",
        alias="library-url",
    )

    creator: NotEmptyString = Field(
        title="Creator",
        description="Name of content creator",
        default="MindTouch",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    file_name: NotEmptyString = Field(
        title="ZIM filename",
        description="ZIM filename. Do not input trailing `.zim`, it "
        "will be automatically added. Defaults to {name}_{period}",
        alias="file-name",
        default="{name_period}",
    )

    name: NotEmptyString = Field(
        title="ZIM name",
        description="Name of the ZIM.",
    )

    title: ZIMTitle = Field(
        title="ZIM title",
        description="Title of the ZIM.",
        alias="zim-title",
    )

    description: ZIMDescription = Field(
        title="ZIM description",
        description="Description of the ZIM.",
        alias="zim-description",
    )

    long_description: ZIMLongDescription = Field(
        title="ZIM long description",
        description="Long description of the ZIM.",
        alias="zim-long-description",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description="A semicolon (;) delimited list of tags to add to the ZIM.",
    )

    secondary_color: NotEmptyString = Field(
        title="Secondary color",
        description="Secondary (background) color of ZIM UI. Default: '#FFFFFF'",
        alias="secondary-color",
    )

    page_id_include: NotEmptyString = Field(
        title="Page ID include",
        description="CSV of page ids to include. Parent pages will be included "
        "as well for proper navigation, up to root (or subroot if --root-page-id is"
        " set). Can be combined with --page-title-include (pages with matching "
        "title or id will be included)",
        alias="page-id-include",
    )

    page_title_include: NotEmptyString = Field(
        title="Page title include regex",
        description="Includes only pages with title matching the given regular "
        "expression, and their parent pages for proper navigation, up to root (or "
        "subroot if --root-page-id is set). Can be combined with --page-id-include "
        "(pages with matching title or id will be included)",
        alias="page-title-include",
    )

    page_title_exclude: NotEmptyString = Field(
        title="Page title exclude regex",
        description="Excludes pages with title matching the given regular expression",
        alias="page-title-exclude",
    )

    root_page_id: NotEmptyString = Field(
        title="Root page ID",
        description="ID of the root page to include in ZIM. Only this page and "
        "its subpages will be included in the ZIM",
        alias="root-page-id",
    )

    illustration_url: AnyUrl = Field(
        title="Illustration URL",
        description="URL to illustration to use for ZIM illustration and favicon",
        alias="illustration-url",
    )

    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
        alias="optimization-cache",
    )

    assets_workers: int = Field(
        title="Asset workers",
        description="Number of parallel workers for asset processing. Default: 10",
        alias="assets-workers",
        default=10,
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )

    bad_assets_regex: NotEmptyString = Field(
        title="Bad assets regex",
        description="Regular expression of asset URLs known to not be available."
        "Case insensitive.",
        alias="bad-assets-regex",
    )

    bad_assets_threshold: int = Field(
        title="Bad assets threshold",
        description="[dev] Number of assets allowed to fail to download before "
        "failing the scraper. Assets already excluded with --bad-assets-regex are "
        "not counted for this threshold. Defaults to 10 assets.",
        alias="bad-assets-threshold",
        default=10,
    )

    stats_filename: NotEmptyString = Field(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
        alias="stats-filename",
        default="/output/task_progress.json",
        validate_default=True,
        pattern=r"^/output/task_progress\.json$",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
        default="/output",
        validate_default=True,
        pattern=r"^/output$",
    )
