from marshmallow import fields, validate

from common.schemas import SerializableSchema, StringEnum
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
)


class OpenedxFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    course_url = fields.Url(
        metadata={
            "label": "Course URL",
            "description": "URL of the course you wnat to scrape",
        },
        data_key="course-url",
        required=True,
    )

    email = fields.String(
        metadata={
            "label": "Registered e-mail",
            "description": "The registered e-mail ID on the openedx instance",
        },
        data_key="email",
        required=True,
    )

    password = fields.String(
        metadata={
            "label": "Password",
            "description": "Password to the account registered on the openedx instance",
            "secret": True,
        },
        data_key="password",
        required=True,
    )

    instance_login_page = fields.String(
        metadata={
            "label": "Login page path",
            "description": "The login path in the instance. Must start with /",
            "placeholder": "/login_ajax",
        },
        data_key="instance-login-page",
    )

    instance_course_page = fields.String(
        metadata={
            "label": "Course page path",
            "description": (
                "The path to the course page after the course ID. Must start with /"
            ),
            "placeholder": "/course",
        },
        data_key="instance-course-page",
    )

    instance_course_prefix = fields.String(
        metadata={
            "label": "Course prefix path",
            "description": (
                "The prefix in the path before the course ID. Must start and end with /"
            ),
            "placeholder": "/courses/",
        },
        data_key="instance-course-prefix",
    )

    favicon_url = fields.Url(
        metadata={
            "label": "Favicon URL",
            "description": (
                "URL pointing to a favicon image. Recommended size >= (48px x 48px)"
            ),
            "placeholder": (
                "https://github.com/edx/edx-platform/raw/master/lms/static/images/"
                "favicon.ico"
            ),
        },
        data_key="favicon-url",
    )

    ignore_missing_xblocks = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Ignore unsupported xblocks",
            "description": "Ignore unsupported content (xblock(s))",
        },
        data_key="ignore-missing-xblocks",
    )

    add_wiki = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Include wiki",
            "description": "Add wiki (if available) to the ZIM",
        },
        data_key="add-wiki",
    )

    add_forum = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Include forum",
            "description": "Add forum/discussion (if available) to the ZIM",
        },
        data_key="add-forum",
    )

    remove_seq_nav = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "No top sequential navigation",
            "description": "Remove the top sequential navigation bar in the ZIM",
        },
        data_key="remove-seq-nav",
    )

    video_format = StringEnum(
        metadata={
            "label": "Video format",
            "description": "Format to download/transcode video to. webm is smaller",
        },
        validate=validate.OneOf(["webm", "mp4"]),
        data_key="format",
    )

    low_quality = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Low Quality",
            "description": "Re-encode video using stronger compression",
        },
        data_key="low-quality",
    )

    autoplay = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Autoplay videos",
            "description": (
                "Enable autoplay on videos. Behavior differs on platforms/browsers"
            ),
        },
        data_key="autoplay",
    )

    name = fields.String(
        metadata={
            "label": "Name",
            "description": (
                "ZIM name. Used as identifier and filename (date will be appended)"
            ),
            "placeholder": "topic_eng",
        },
        data_key="name",
        required=True,
    )

    title = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. Based on MOOC otherwise",
        },
        data_key="title",
    )

    description = fields.String(
        metadata={
            "label": "Description",
            "description": "Custom description for your ZIM. Based on MOOC otherwise",
        },
        data_key="description",
        validate=validate_zim_description,
    )

    creator = fields.String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Defaults to edX",
        },
        data_key="creator",
    )

    tags = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": (
                "List of comma-separated Tags for the ZIM file. category:other, and "
                "openedx added automatically"
            ),
        },
        data_key="tags",
    )

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": (
                "URL with credentials and bucket name to S3 Optimization Cache"
            ),
            "secret": True,
        },
        data_key="optimization-cache",
    )

    use_any_optimized_version = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Use any optimized version",
            "description": "Use the cached files if present, whatever the version",
        },
        data_key="use-any-optimized-version",
    )

    output = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file(s). Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
        data_key="output",
    )

    tmp_dir = fields.String(
        metadata={
            "label": "Temp folder",
            "description": (
                "Where to create temporay build folder. Leave it as `/output`"
            ),
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
        data_key="tmp-dir",
    )

    zim_file = fields.String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on ZIM name if not provided)",
        },
        data_key="zim-file",
        validate=validate_zim_filename,
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )

    threads = fields.Integer(
        metadata={
            "label": "Threads",
            "description": "Number of parallel threads to use while downloading",
        },
        validate=validate.Range(min=1),
    )

    locale = fields.String(
        metadata={
            "label": "Locale",
            "description": "The locale to use for the translations in ZIM",
        }
    )
