from enum import StrEnum
from typing import Literal

from pydantic import AnyUrl, EmailStr, Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    OptionalNotEmptyString,
    OptionalS3OptimizationCache,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMOutputFolder,
    OptionalZIMTitle,
    ZIMSecretStr,
)


class VideoFormat(StrEnum):
    WEBM = "webm"
    MP4 = "mp4"


class OpenedxFlagsSchema(DashModel):
    offliner_id: Literal["openedx"]

    course_url: AnyUrl = Field(
        title="Course URL",
        description="URL of the course you wnat to scrape",
    )

    email: EmailStr = Field(
        title="Registered e-mail",
        description="The registered e-mail ID on the openedx instance",
    )

    password: ZIMSecretStr = Field(
        title="Password",
        description="Password to the account registered on the openedx instance",
    )

    instance_login_page: OptionalNotEmptyString = OptionalField(
        title="Login page path",
        description="The login path in the instance. Must start with /",
    )

    instance_course_page: OptionalNotEmptyString = OptionalField(
        title="Course page path",
        description=(
            "The path to the course page after the course ID. Must start with /"
        ),
    )

    instance_course_prefix: OptionalNotEmptyString = OptionalField(
        title="Course prefix path",
        description=(
            "The prefix in the path before the course ID. Must start and end with /"
        ),
    )

    favicon_url: AnyUrl | None = OptionalField(
        title="Favicon URL",
        description=(
            "URL pointing to a favicon image. Recommended size >= (48px x 48px)"
        ),
    )

    ignore_missing_xblocks: bool | None = OptionalField(
        title="Ignore unsupported xblocks",
        description="Ignore unsupported content (xblock(s))",
    )

    add_wiki: bool | None = OptionalField(
        title="Include wiki",
        description="Add wiki (if available) to the ZIM",
    )

    add_forum: bool | None = OptionalField(
        title="Include forum",
        description="Add forum/discussion (if available) to the ZIM",
    )

    remove_seq_nav: bool | None = OptionalField(
        title="No top sequential navigation",
        description="Remove the top sequential navigation bar in the ZIM",
    )

    video_format: VideoFormat | None = OptionalField(
        title="Video format",
        description="Format to download/transcode video to. webm is smaller",
    )

    low_quality: bool | None = OptionalField(
        title="Low Quality",
        description="Re-encode video using stronger compression",
    )

    autoplay: bool | None = OptionalField(
        title="Autoplay videos",
        description=(
            "Enable autoplay on videos. Behavior differs on platforms/browsers"
        ),
    )

    name: NotEmptyString = Field(
        title="Name",
        description=(
            "ZIM name. Used as identifier and filename (date will be appended)"
        ),
    )

    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for your ZIM. Based on MOOC otherwise",
    )

    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Custom description for your ZIM. Based on MOOC otherwise",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Content Creator",
        description="Name of content creator. Defaults to edX",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description='Custom publisher name (ZIM metadata). "openZIM" otherwise',
    )

    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description=(
            "List of comma-separated Tags for the ZIM file. category:other, and "
            "openedx added automatically"
        ),
    )

    optimization_cache: OptionalS3OptimizationCache = OptionalField(
        title="Optimization Cache URL",
        description="URL with credentials and bucket name to S3 Optimization Cache",
    )

    use_any_optimized_version: bool | None = OptionalField(
        title="Use any optimized version",
        description="Use the cached files if present, whatever the version",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
    )

    tmp_dir: OptionalNotEmptyString = OptionalField(
        title="Temp folder",
        description="Where to create temporay build folder. Leave it as `/output`",
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
