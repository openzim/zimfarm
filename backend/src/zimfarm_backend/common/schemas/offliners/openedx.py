from typing import Literal

from pydantic import Field
from pydantic.types import AnyUrl, EmailStr, SecretStr

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    S3OptimizationCache,
    ZIMDescription,
    ZIMFileName,
    ZIMOutputFolder,
    ZIMTitle,
)


class OpenedxFlagsSchema(BaseModel):
    course_url: AnyUrl = Field(
        title="Course URL",
        description="URL of the course you wnat to scrape",
        alias="course-url",
    )

    email: EmailStr = Field(
        title="Registered e-mail",
        description="The registered e-mail ID on the openedx instance",
        alias="email",
    )

    password: SecretStr = Field(
        title="Password",
        description="Password to the account registered on the openedx instance",
        alias="password",
    )

    instance_login_page: NotEmptyString = Field(
        title="Login page path",
        description="The login path in the instance. Must start with /",
        alias="instance-login-page",
        default="/login_ajax",
    )

    instance_course_page: NotEmptyString = Field(
        title="Course page path",
        description=(
            "The path to the course page after the course ID. Must start with /"
        ),
        alias="instance-course-page",
        default="/course",
    )

    instance_course_prefix: NotEmptyString = Field(
        title="Course prefix path",
        description=(
            "The prefix in the path before the course ID. Must start and end with /"
        ),
        alias="instance-course-prefix",
        default="/courses/",
    )

    favicon_url: AnyUrl = Field(
        title="Favicon URL",
        description=(
            "URL pointing to a favicon image. Recommended size >= (48px x 48px)"
        ),
        default=(
            "https://github.com/edx/edx-platform/raw/master/lms/static/images/"
            "favicon.ico"
        ),
        alias="favicon-url",
    )

    ignore_missing_xblocks: bool = Field(
        title="Ignore unsupported xblocks",
        description="Ignore unsupported content (xblock(s))",
        alias="ignore-missing-xblocks",
    )

    add_wiki: bool = Field(
        title="Include wiki",
        description="Add wiki (if available) to the ZIM",
        alias="add-wiki",
    )

    add_forum: bool = Field(
        title="Include forum",
        description="Add forum/discussion (if available) to the ZIM",
        alias="add-forum",
    )

    remove_seq_nav: bool = Field(
        title="No top sequential navigation",
        description="Remove the top sequential navigation bar in the ZIM",
        alias="remove-seq-nav",
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
        title="Autoplay videos",
        description=(
            "Enable autoplay on videos. Behavior differs on platforms/browsers"
        ),
        alias="autoplay",
    )

    name: NotEmptyString = Field(
        title="Name",
        description=(
            "ZIM name. Used as identifier and filename (date will be appended)"
        ),
        alias="name",
        default="topic_eng",
    )

    title: ZIMTitle = Field(
        title="Title",
        description="Custom title for your ZIM. Based on MOOC otherwise",
        alias="title",
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Custom description for your ZIM. Based on MOOC otherwise",
        alias="description",
    )

    creator: NotEmptyString = Field(
        title="Content Creator",
        description="Name of content creator. Defaults to edX",
        alias="creator",
        default="edX",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        alias="publisher",
        default="openZIM",
    )

    tags: NotEmptyString = Field(
        title="ZIM Tags",
        description=(
            "List of comma-separated Tags for the ZIM file. category:other, and "
            "openedx added automatically"
        ),
        alias="tags",
    )

    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description="URL with credentials and bucket name to S3 Optimization Cache",
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
        alias="output",
        default="/output",
        validate_default=True,
    )

    tmp_dir: NotEmptyString = Field(
        title="Temp folder",
        description="Where to create temporay build folder. Leave it as `/output`",
        alias="tmp-dir",
        default="/output",
        validate_default=True,
    )

    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on ZIM name if not provided)",
        alias="zim-file",
        validate_default=True,
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
