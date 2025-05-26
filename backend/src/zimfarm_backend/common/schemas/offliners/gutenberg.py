from common.schemas import BaseModel
from pydantic import Field

from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    S3OptimizationCache,
    ZIMDescription,
    ZIMOutputFolder,
    ZIMTitle,
)


class GutenbergFlagsSchema(BaseModel):
    languages: NotEmptyString = Field(
        title="Languages",
        description=(
            "Comma-separated list of lang codes to filter "
            "export to (preferably ISO 639-1, else ISO 639-3) Defaults to all"
        ),
        default="all",
    )

    formats: NotEmptyString = Field(
        title="Formats",
        description=(
            "Comma-separated list of formats to filter export to (epub,"
            " html, pdf, all) Defaults to all"
        ),
        default="all",
    )

    zim_title: ZIMTitle = Field(
        title="Title",
        description="Custom title for your project and ZIM.",
        alias="zim-title",
    )

    zim_desc: ZIMDescription = Field(
        title="Description",
        description="Description for ZIM",
        alias="zim-desc",
    )

    books: NotEmptyString = Field(
        title="Books",
        description=(
            "Filter to only specific books ; separated by commas, or dashes "
            "for intervals. Defaults to all"
        ),
        default="all",
    )

    concurrency: int = Field(
        title="Concurrency",
        description="Number of concurrent threads to use",
    )

    dlc: int = Field(
        title="Download Concurrency",
        description=("Number of parallel downloads to run (overrides concurrency)"),
        alias="dlc",
    )

    # /!\ we are using a boolean flag for this while the actual option
    # expect an output folder for the ZIM files.
    # Given we can't set the output dir for regular mode, we're using this
    # flag to switch between the two and the path is set to the mount point
    # in command_for() (offliners.py)
    one_language_one_zim: bool | ZIMOutputFolder = Field(
        title="Multiple ZIMs",
        description="Create one ZIM per language",
        alias="one-language-one-zim",
    )

    no_index: bool = Field(
        title="No Index",
        description="Do not create full-text index within ZIM file",
        alias="no-index",
    )

    title_search: bool = Field(
        title="Title search",
        description="Search by title feature (⚠️ does not scale)",
        alias="title-search",
    )

    bookshelves: bool = Field(
        title="Bookshelves",
        description="Browse by bookshelves feature",
    )

    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
        alias="optimization-cache",
    )

    use_any_optimized_version: bool = Field(
        title="Use any optimized version",
        description="Use any optimized version",
        alias="use-any-optimized-version",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )
