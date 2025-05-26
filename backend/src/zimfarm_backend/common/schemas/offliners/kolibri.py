from pydantic import Field
from pydantic.types import AnyUrl

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


class KolibriFlagsSchema(BaseModel):
    channel_id: NotEmptyString = Field(
        title="Channel ID",
        description="The Kolibri channel ID that you want to scrape",
        alias="channel-id",
    )

    root_id: NotEmptyString = Field(
        title="Root ID",
        description="The node ID (usually Topic) from where to start "
        "the scraper. Defaults to the root of the channel.",
        alias="root-id",
    )

    lang: NotEmptyString = Field(
        title="Language",
        description="ISO-639-3 (3 chars) language code of content. "
        "If unspecified, will attempt to detect from main page, or use 'eng'",
        default="eng",
    )

    name: NotEmptyString = Field(
        title="Name",
        description="ZIM name. Used as identifier and filename (date will be appended)",
    )

    title: ZIMTitle | None = Field(
        title="Title",
        description="Custom title for your ZIM. Kolibri channel name otherwise",
        default=None,
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Custom description for your ZIM. "
        "Kolibri channel description otherwise",
    )

    long_description: ZIMLongDescription = Field(
        title="Long description",
        description="Custom long description for your ZIM. "
        "If not provided, either not set or Kolibri channel description if it was "
        "too long to fit entirely in ZIM description",
        alias="long-description",
    )

    favicon: AnyUrl | None = Field(
        title="Favicon",
        description="URL for Favicon. Kolibri channel thumbnail otherwise "
        "or default Kolobri logo if missing",
        default=None,
    )

    css: AnyUrl | None = Field(
        title="Custom CSS",
        description="URL to a single CSS file to be included in all pages "
        "(but not on kolibri-html-content ones). "
        "Inlude external resources using data URL.",
        default=None,
    )

    about: AnyUrl | None = Field(
        title="Custom About",
        description="URL to a single HTML file to use as an about page. "
        "Place everythong inside `body .container` "
        "(including stylesheets and scripts) "
        "as only this and your <title> will be merged into the actual about page. "
        "Remember to include images inline using data URL.",
        default=None,
    )

    creator: NotEmptyString = Field(
        title="Content Creator",
        description="Name of content creator. Kolibri "
        "channel author or “Kolibri” otherwise",
        default="Kolibri",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description="List of comma-separated Tags for the ZIM file. "
        "category:other, kolibri, and _videos:yes added automatically",
    )

    use_webm: bool = Field(
        title="Use WebM",
        description="Kolibri videos are in mp4. Choosing webm will require "
        "videos to be re-encoded. Result will be slightly smaller and of lower "
        "quality. WebM support is bundled in the ZIM so videos "
        "will be playable on every platform.",
        alias="use-webm",
    )

    low_quality: bool = Field(
        title="Low quality",
        description="Uses only the `low_res` version of videos if available. "
        "If not, recompresses using agressive compression.",
        alias="low-quality",
    )

    autoplay: bool = Field(
        title="Autoplay",
        description="Enable autoplay on video and audio articles. "
        "Behavior differs on platforms/browsers.",
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

    threads: int = Field(
        title="Threads",
        description="Number of threads to use to handle nodes concurrently. "
        "Increase to speed-up I/O operations (disk, network). Default: 1",
        default=1,
    )

    processes: int = Field(
        title="Processes",
        description="Number of processes to dedicate to media optimizations. "
        "Default: 1",
        default=1,
    )

    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
        alias="optimization-cache",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )
