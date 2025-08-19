from typing import Literal

from pydantic import AnyUrl, Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    OptionalNotEmptyString,
    OptionalSecretUrl,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    OptionalZIMTitle,
    ZIMName,
)


class KolibriFlagsSchema(DashModel):
    offliner_id: Literal["kolibri"] = Field(alias="offliner_id")

    channel_id: NotEmptyString = Field(
        title="Channel ID",
        description="The Kolibri channel ID that you want to scrape",
    )

    root_id: OptionalNotEmptyString = OptionalField(
        title="Root ID",
        description="The node ID (usually Topic) from where to start "
        "the scraper. Defaults to the root of the channel.",
    )

    lang: OptionalNotEmptyString = OptionalField(
        title="Language",
        description="ISO-639-3 (3 chars) language code of content. "
        "If unspecified, will attempt to detect from main page, or use 'eng'",
    )

    name: ZIMName = Field(
        title="Name",
        description="ZIM name. Used as identifier and filename (date will be appended)",
    )

    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for your ZIM. Kolibri channel name otherwise",
    )

    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Custom description for your ZIM. "
        "Kolibri channel description otherwise",
    )

    long_description: OptionalZIMLongDescription = OptionalField(
        title="Long description",
        description="Custom long description for your ZIM. "
        "If not provided, either not set or Kolibri channel description if it was "
        "too long to fit entirely in ZIM description",
    )

    favicon: AnyUrl | None = OptionalField(
        title="Favicon",
        description="URL for Favicon. Kolibri channel thumbnail otherwise "
        "or default Kolobri logo if missing",
    )

    css: AnyUrl | None = OptionalField(
        title="Custom CSS",
        description="URL to a single CSS file to be included in all pages "
        "(but not on kolibri-html-content ones). "
        "Inlude external resources using data URL.",
    )

    about: AnyUrl | None = OptionalField(
        title="Custom About",
        description="URL to a single HTML file to use as an about page. "
        "Place everythong inside `body .container` "
        "(including stylesheets and scripts) "
        "as only this and your <title> will be merged into the actual about page. "
        "Remember to include images inline using data URL.",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Content Creator",
        description="Name of content creator. Kolibri "
        'channel author or "Kolibri" otherwise',
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description='Custom publisher name (ZIM metadata). "openZIM" otherwise',
    )

    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="List of comma-separated Tags for the ZIM file. "
        "category:other, kolibri, and _videos:yes added automatically",
    )

    use_webm: bool | None = OptionalField(
        title="Use WebM",
        description="Kolibri videos are in mp4. Choosing webm will require "
        "videos to be re-encoded. Result will be slightly smaller and of lower "
        "quality. WebM support is bundled in the ZIM so videos "
        "will be playable on every platform.",
    )

    low_quality: bool | None = OptionalField(
        title="Low quality",
        description="Uses only the `low_res` version of videos if available. "
        "If not, recompresses using agressive compression.",
    )

    autoplay: bool | None = OptionalField(
        title="Autoplay",
        description="Enable autoplay on video and audio articles. "
        "Behavior differs on platforms/browsers.",
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

    threads: int | None = OptionalField(
        title="Threads",
        description="Number of threads to use to handle nodes concurrently. "
        "Increase to speed-up I/O operations (disk, network). Default: 1",
    )

    processes: int | None = OptionalField(
        title="Processes",
        description="Number of processes to dedicate to media optimizations. "
        "Default: 1",
    )

    optimization_cache: OptionalSecretUrl = OptionalField(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )
