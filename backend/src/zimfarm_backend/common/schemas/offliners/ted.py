from typing import Literal

from pydantic import Field

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    S3OptimizationCache,
    ZIMDescription,
    ZIMFileName,
    ZIMLongDescription,
    ZIMOutputFolder,
    ZIMTitle,
)


class TedFlagsSchema(BaseModel):
    topics: NotEmptyString = Field(
        title="Topics",
        description=(
            "Comma-separated list of topics to scrape; as given on ted.com/talks. "
            "Pass all for all topics"
        ),
    )

    playlists: NotEmptyString = Field(
        title="TED Playlists",
        description=(
            "Comma-separated list of TED playlist IDs to scrape. Pass all for all "
            "playlists"
        ),
    )

    languages: NotEmptyString = Field(
        title="Languages",
        description=(
            "Comma-separated list of languages to filter videos. Do not "
            "pass this parameter for all languages"
        ),
    )

    subtitles_enough: bool = Field(
        title="Subtitles enough?",
        description=(
            "Whether to include videos that have a subtitle in "
            "requested language(s) if audio is in another language"
        ),
        alias="subtitles-enough",
    )

    subtitles: NotEmptyString = Field(
        title="Subtitles Setting",
        description=(
            "Language setting for subtitles. all: include all available subtitles, "
            "matching (default): only subtitles matching language(s), none: include"
            " no subtitle. Also accepts comma-separated list of language(s)"
        ),
    )

    video_format: Literal["webm", "mp4"] = Field(
        title="Video format",
        description="Format to download/transcode video to. webm is smaller",
        alias="format",
    )

    low_quality: bool = Field(
        title="Low Quality",
        description="Re-encode video using stronger compression",
        alias="low-quality",
    )

    autoplay: bool = Field(
        title="Auto-play",
        description=(
            "Enable autoplay on video articles. Behavior differs on platforms/browsers."
        ),
    )

    name: NotEmptyString = Field(
        title="Name",
        description=(
            "ZIM name. Used as identifier and filename (date will be appended)"
        ),
        default="topic_eng",
    )

    title: ZIMTitle = Field(
        title="Title",
        description="Custom title for your ZIM. Based on selection otherwise",
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Custom description for your ZIM. Based on selection otherwise",
    )

    long_description: ZIMLongDescription = Field(
        title="Long description",
        description=(
            "Custom long description for your ZIM. Based on selection otherwise"
        ),
        alias="long-description",
    )

    creator: NotEmptyString = Field(
        title="Content Creator",
        description="Name of content creator. Defaults to TED",
        default="TED",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description=(
            "List of comma-separated Tags for the ZIM file. category:ted, ted, and"
            " _videos:yes added automatically"
        ),
    )

    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description=("URL with credentials and bucket name to S3 Optimization Cache"),
        alias="optimization-cache",
    )

    use_any_optimized_version: bool = Field(
        title="Use any optimized version",
        description="Use the cached files if present, whatever the version",
        alias="use-any-optimized-version",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
        default="/output",
        validate_default=True,
    )

    tmp_dir: ZIMOutputFolder = Field(
        title="Temp folder",
        description=("Where to create temporay build folder. Leave it as `/output`"),
        default="/output",
        validate_default=True,
        alias="tmp-dir",
    )

    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on ZIM name if not provided)",
        alias="zim-file",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )

    threads: int = Field(
        title="Threads",
        description="Number of parallel threads to use while downloading",
        ge=1,
    )

    locale: NotEmptyString = Field(
        title="Locale",
        description="The locale to use for the translations in ZIM",
    )
