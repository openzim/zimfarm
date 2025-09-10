from typing import Literal

from pydantic import AnyUrl, Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalCommaSeparatedZIMLangCode,
    OptionalField,
    OptionalNotEmptyString,
    OptionalSecretUrl,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    OptionalZIMProgressFile,
    OptionalZIMTitle,
    ZIMName,
    ZIMSecretStr,
)


class YoutubeFlagsSchema(DashModel):
    offliner_id: Literal["youtube"] = Field(alias="offliner_id")

    optimization_cache: OptionalSecretUrl = OptionalField(
        title="Optimization Cache URL",
        description="Technical Flag: S3 Storage URL including credentials and bucket",
    )

    api_key: ZIMSecretStr = Field(
        title="API Key",
        description="Technical flag: Youtube API Token",
    )

    ident: NotEmptyString = Field(
        title="Youtube ID(s)",
        description="Youtube ID(s) of the handle, channel, user, or playlist(s) "
        "to ZIM (depending on the Type chosen below). Only playlist Type support "
        "multiple Youtube IDs and they must be separated by commas.",
        alias="id",
    )

    language: OptionalCommaSeparatedZIMLangCode = OptionalField(
        title="Language",
        description="ISO-639-3 (3 chars) language code of content",
    )

    name: ZIMName = Field(
        title="ZIM Name",
        description="Used as identifier and filename (date will be appended)",
    )

    zim_file: OptionalZIMFileName = OptionalField(
        title="ZIM Filename",
        description="ZIM file name (optional, based on ZIM Name "
        "if not provided). Include {period} to insert date period dynamically",
    )

    title: OptionalZIMTitle = OptionalField(
        title="ZIM Title",
        description="Custom title for your ZIM. "
        "Default to Channel name (of first video if playlists)",
    )

    description: OptionalZIMDescription = OptionalField(
        title="ZIM Description",
        description="Description (up to 80 chars) for ZIM",
    )

    long_description: OptionalZIMLongDescription = OptionalField(
        title="ZIM Long Description",
        description="Long description (up to 4000 chars) for ZIM",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Content Creator",
        description="Name of content creator. Defaults to Channel name "
        'or "Youtube Channels"',
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description='Custom publisher name (ZIM metadata). "openZIM" otherwise',
    )

    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="List of comma-separated Tags for the ZIM file. "
        "_videos:yes added automatically",
    )

    dateafter: OptionalNotEmptyString = OptionalField(
        title="Only after date",
        description="Custom filter to download videos uploaded on "
        "or after specified date. Format: YYYYMMDD or "
        "(now|today)[+-][0-9](day|week|month|year)(s)?",
    )

    video_format: Literal["webm", "mp4"] | None = OptionalField(
        title="Video format",
        description="Format to download/transcode video to. webm is smaller",
        alias="format",
    )

    low_quality: bool | None = OptionalField(
        title="Low Quality",
        description="Re-encode video using stronger compression",
    )

    use_any_optimized_version: bool | None = OptionalField(
        title="Use any optimized version",
        description="Use the cached files if present, whatever the version",
    )

    all_subtitles: bool | None = OptionalField(
        title="All Subtitles",
        description="Include auto-generated subtitles",
    )

    pagination: int | None = OptionalField(
        title="Pagination",
        description="Number of videos per page (40 otherwise)",
    )

    profile: AnyUrl | None = OptionalField(
        title="Profile Image",
        description="Custom profile image. Squared. Will be resized to 100x100px",
    )

    banner: AnyUrl | None = OptionalField(
        title="Banner Image",
        description="Custom banner image. Will be resized to 1060x175px",
    )

    main_color: OptionalNotEmptyString = OptionalField(
        title="Main Color",
        description="Custom color. Hex/HTML syntax (#DEDEDE). "
        "Default to main color of profile image.",
    )

    secondary_color: OptionalNotEmptyString = OptionalField(
        title="Secondary Color",
        description="Custom secondary color. Hex/HTML syntax (#DEDEDE). "
        "Default to secondary color of profile image.",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )

    concurrency: int | None = OptionalField(
        title="Concurrency",
        description="Expert flag: Number of concurrent threads to use",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="Technical flag: Output folder for ZIM file(s). Leave it "
        "as `/output`",
    )

    stats_filename: OptionalZIMProgressFile = OptionalField(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
    )

    tmp_dir: OptionalZIMOutputFolder = OptionalField(
        title="Temp folder",
        description="Technical flag: Where to create temporay build folder. "
        "Leave it as `/output`",
    )
