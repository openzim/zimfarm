import re
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    Field,
    ValidationInfo,
    WrapValidator,
    field_validator,
    model_validator,
)

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    OptionalCommaSeparatedZIMLangCode,
    OptionalField,
    OptionalNotEmptyString,
    OptionalSecretUrl,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    OptionalZIMTitle,
    ZIMName,
    enum_member,
)


class VideoFormat(StrEnum):
    WEBM = "webm"
    MP4 = "mp4"


VideoFormatValue = Annotated[VideoFormat, WrapValidator(enum_member(VideoFormat))]


class TedFlagsSchema(DashModel):
    offliner_id: Literal["ted"] = Field(alias="offliner_id")

    topics: OptionalNotEmptyString = OptionalField(
        title="Topics",
        description=(
            "Comma-separated list of topics to scrape; as given on ted.com/talks. "
            "Pass all for all topics. Exclusive with playlists and links, only one "
            "must be set."
        ),
    )

    playlists: OptionalNotEmptyString = OptionalField(
        title="TED Playlists",
        description=(
            "Comma-separated list of TED playlist IDs to scrape. Pass all for all "
            "playlists. Exclusive with topics and links, only one must set."
        ),
    )

    links: OptionalNotEmptyString = OptionalField(
        title="Links",
        description=(
            "Comma-separated TED talk URLs to scrape, each in the format: "
            "https://www.ted.com/talks/<talk_slug>. Exclusive with topics and "
            "playlists, only one must be set."
        ),
    )

    languages: OptionalCommaSeparatedZIMLangCode = OptionalField(
        title="Languages",
        description=(
            "Comma-separated list of ISO-639-3 language codes to filter videos. Do not "
            "pass this parameter for all languages"
        ),
    )

    subtitles_enough: bool | None = OptionalField(
        title="Subtitles enough?",
        description=(
            "Whether to include videos that have a subtitle in "
            "requested language(s) if audio is in another language"
        ),
    )

    subtitles: OptionalNotEmptyString = OptionalField(
        title="Subtitles Setting",
        description=(
            "Language setting for subtitles. all: include all available subtitles, "
            "matching (default): only subtitles matching language(s), none: include"
            " no subtitle. Also accepts comma-separated list of language(s)"
        ),
    )

    video_format: VideoFormatValue | None = OptionalField(
        title="Video format",
        description="Format to download/transcode video to. webm is smaller",
        alias="format",
    )

    low_quality: bool | None = OptionalField(
        title="Low Quality",
        description="Re-encode video using stronger compression",
    )

    autoplay: bool | None = OptionalField(
        title="Auto-play",
        description=(
            "Enable autoplay on video articles. Behavior differs on platforms/browsers."
        ),
    )

    name: ZIMName = Field(
        title="Name",
        description=(
            "ZIM name. Used as identifier and filename (date will be appended)"
        ),
    )

    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for your ZIM. Based on selection otherwise",
    )

    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Custom description for your ZIM. Based on selection otherwise",
    )

    long_description: OptionalZIMLongDescription = OptionalField(
        title="Long description",
        description=(
            "Custom long description for your ZIM. Based on selection otherwise"
        ),
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Content Creator",
        description="Name of content creator. Defaults to TED",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description='Custom publisher name (ZIM metadata). "openZIM" otherwise',
    )

    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description=(
            "List of comma-separated Tags for the ZIM file. category:ted, ted, and"
            " _videos:yes added automatically"
        ),
    )

    optimization_cache: OptionalSecretUrl = OptionalField(
        title="Optimization Cache URL",
        description=("URL with credentials and bucket name to S3 Optimization Cache"),
    )

    use_any_optimized_version: bool | None = OptionalField(
        title="Use any optimized version",
        description="Use the cached files if present, whatever the version",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
    )

    tmp_dir: OptionalZIMOutputFolder = OptionalField(
        title="Temp folder",
        description=("Where to create temporay build folder. Leave it as `/output`"),
    )

    zim_file: OptionalZIMFileName = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on ZIM name if not provided)",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )

    threads: int | None = OptionalField(
        title="Threads",
        description="Number of parallel threads to use while downloading",
        ge=1,
    )

    locale: OptionalNotEmptyString = OptionalField(
        title="Locale",
        description="The locale to use for the translations in ZIM",
    )

    language_threshold: float | None = OptionalField(
        title="Language Threshold",
        description=(
            "Add language in ZIM metadata only if present in at least "
            "this percentage of videos. Number between 0 and 1. "
            "Defaults to 0.5: language must be used in 50% of videos to be considered "
            "as ZIM language."
        ),
        ge=0,
        le=1,
    )

    @field_validator("links", mode="after")
    @classmethod
    def validate_links(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return value

        context = info.context
        if context and context.get("skip_validation"):
            return value

        for link in value.split(","):
            if not re.match(r"^https://www\.ted\.com/talks/[a-zA-Z0-9_-]+$", link):
                raise ValueError(f"Invalid TED talk URL: '{link}'")
        return value

    @model_validator(mode="after")
    def check_exclusive_fields(self, info: ValidationInfo) -> Self:
        context = info.context
        if context and context.get("skip_validation"):
            return self

        set_fields = [
            name
            for name in ("links", "topics", "playlists")
            if getattr(self, name) is not None
        ]

        if len(set_fields) != 1:
            raise ValueError(
                "One and only one of 'links', 'topics', or 'playlists' must be set"
            )

        return self
