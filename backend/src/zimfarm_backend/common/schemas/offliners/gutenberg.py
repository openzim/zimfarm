from typing import Literal

from pydantic import Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    OptionalField,
    OptionalNotEmptyString,
    OptionalS3OptimizationCache,
    OptionalZIMDescription,
    OptionalZIMTitle,
)


class GutenbergFlagsSchema(DashModel):
    offliner_id: Literal["gutenberg"] = Field(exclude=True)

    languages: OptionalNotEmptyString = OptionalField(
        title="Languages",
        description=(
            "Comma-separated list of lang codes to filter "
            "export to (preferably ISO 639-1, else ISO 639-3) Defaults to all"
        ),
    )

    formats: OptionalNotEmptyString = OptionalField(
        title="Formats",
        description=(
            "Comma-separated list of formats to filter export to (epub,"
            " html, pdf, all) Defaults to all"
        ),
    )

    zim_title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for your project and ZIM.",
    )

    zim_desc: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Description for ZIM",
    )

    books: OptionalNotEmptyString = OptionalField(
        title="Books",
        description=(
            "Filter to only specific books ; separated by commas, or dashes "
            "for intervals. Defaults to all"
        ),
    )

    concurrency: int | None = OptionalField(
        title="Concurrency",
        description="Number of concurrent threads to use",
    )

    dlc: int | None = OptionalField(
        title="Download Concurrency",
        description=("Number of parallel downloads to run (overrides concurrency)"),
    )

    # /!\ we are using a boolean flag for this while the actual option
    # expect an output folder for the ZIM files.
    # Given we can't set the output dir for regular mode, we're using this
    # flag to switch between the two and the path is set to the mount point
    # in command_for() (offliners.py)
    one_language_one_zim: bool | None = OptionalField(
        title="Multiple ZIMs",
        description="Create one ZIM per language",
    )

    no_index: bool | None = OptionalField(
        title="No Index",
        description="Do not create full-text index within ZIM file",
    )

    title_search: bool | None = OptionalField(
        title="Title search",
        description="Search by title feature (⚠️ does not scale)",
    )

    bookshelves: bool | None = OptionalField(
        title="Bookshelves",
        description="Browse by bookshelves feature",
    )

    optimization_cache: OptionalS3OptimizationCache = OptionalField(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
    )

    use_any_optimized_version: bool | None = OptionalField(
        title="Use any optimized version",
        description="Use any optimized version",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
    )
