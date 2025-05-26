from typing import Literal

from pydantic import Field
from pydantic.types import AnyUrl, SecretStr

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


class YoutubeFlagsSchema(BaseModel):
    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description="Technical Flag: S3 Storage URL including credentials and bucket",
        alias="optimization-cache",
    )

    api_key: SecretStr = Field(
        title="API Key",
        description="Technical flag: Youtube API Token",
        alias="api-key",
    )

    id: NotEmptyString = Field(
        title="Youtube ID(s)",
        description="Youtube ID(s) of the handle, channel, user, or playlist(s) "
        "to ZIM (depending on the Type chosen below). Only playlist Type support "
        "multiple Youtube IDs and they must be separated by commas.",
        alias="id",
    )

    language: NotEmptyString = Field(
        title="Language",
        description="ISO-639-3 (3 chars) language code of content",
    )

    name: NotEmptyString = Field(
        title="ZIM Name",
        description="Used as identifier and filename (date will be appended)",
        alias="name",
        default="mychannel_eng_all",
    )

    zim_file: ZIMFileName = Field(
        title="ZIM Filename",
        description="ZIM file name (optional, based on ZIM Name "
        "if not provided). Include {period} to insert date period dynamically",
        alias="zim-file",
    )

    title: ZIMTitle = Field(
        title="ZIM Title",
        description="Custom title for your ZIM. "
        "Default to Channel name (of first video if playlists)",
    )

    description: ZIMDescription = Field(
        title="ZIM Description",
        description="Description (up to 80 chars) for ZIM",
        alias="description",
    )

    long_description: ZIMLongDescription = Field(
        title="ZIM Long Description",
        description="Long description (up to 4000 chars) for ZIM",
        alias="long-description",
    )

    creator: NotEmptyString = Field(
        title="Content Creator",
        description="Name of content creator. Defaults to Channel name "
        "or “Youtube Channels”",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description="List of comma-separated Tags for the ZIM file. "
        "_videos:yes added automatically",
    )

    dateafter: NotEmptyString = Field(
        title="Only after date",
        description="Custom filter to download videos uploaded on "
        "or after specified date. Format: YYYYMMDD or "
        "(now|today)[+-][0-9](day|week|month|year)(s)?",
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

    use_any_optimized_version: bool = Field(
        title="Use any optimized version",
        description="Use the cached files if present, whatever the version",
        alias="use-any-optimized-version",
    )

    all_subtitles: bool = Field(
        title="All Subtitles",
        description="Include auto-generated subtitles",
        alias="all-subtitles",
    )

    pagination: int = Field(
        title="Pagination",
        description="Number of videos per page (40 otherwise)",
    )

    profile: AnyUrl = Field(
        title="Profile Image",
        description="Custom profile image. Squared. Will be resized to 100x100px",
    )

    banner: AnyUrl = Field(
        title="Banner Image",
        description="Custom banner image. Will be resized to 1060x175px",
    )

    main_color: NotEmptyString = Field(
        title="Main Color",
        description="Custom color. Hex/HTML syntax (#DEDEDE). "
        "Default to main color of profile image.",
        alias="main-color",
    )

    secondary_color: NotEmptyString = Field(
        title="Secondary Color",
        description="Custom secondary color. Hex/HTML syntax (#DEDEDE). "
        "Default to secondary color of profile image.",
        alias="secondary-color",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )

    concurrency: int = Field(
        title="Concurrency",
        description="Expert flag: Number of concurrent threads to use",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description="Technical flag: Output folder for ZIM file(s). Leave it "
        "as `/output`",
        default="/output",
        validate_default=True,
    )

    stats_filename: NotEmptyString = Field(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
        default="/output/task_progress.json",
        validate_default=True,
        pattern=r"^/output/task_progress\.json$",
        alias="stats-filename",
    )

    tmp_dir: ZIMOutputFolder = Field(
        title="Temp folder",
        description="Technical flag: Where to create temporay build folder. "
        "Leave it as `/output`",
        default="/output",
        validate_default=True,
        alias="tmp-dir",
        pattern=r"^/output$",
    )
