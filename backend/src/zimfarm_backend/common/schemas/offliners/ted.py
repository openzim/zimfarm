from marshmallow import fields, validate

from common.schemas import LongString, SerializableSchema, String, StringEnum
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
    validate_zim_longdescription,
    validate_zim_title,
)


class TedFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    topics = String(
        metadata={
            "label": "Topics",
            "description": (
                "Comma-separated list of topics to scrape; as given on ted.com/talks. "
                "Pass all for all topics"
            ),
        },
    )

    playlists = String(
        metadata={
            "label": "TED Playlists",
            "description": (
                "Comma-separated list of TED playlist IDs to scrape. Pass all for all "
                "playlists"
            ),
        },
    )

    languages = String(
        metadata={
            "label": "Languages",
            "description": "Comma-separated list of languages to filter videos. Do not "
            "pass this parameter for all languages",
        },
    )

    subtitles_enough = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Subtitles enough?",
            "description": (
                "Whether to include videos that have a subtitle in "
                "requested language(s) if audio is in another language"
            ),
        },
        data_key="subtitles-enough",
    )

    subtitles = String(
        metadata={
            "label": "Subtitles Setting",
            "description": (
                "Language setting for subtitles. all: include all available subtitles, "
                "matching (default): only subtitles matching language(s), none: include"
                " no subtitle. Also accepts comma-separated list of language(s)"
            ),
        },
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
            "label": "Auto-play",
            "description": (
                "Enable autoplay on video articles. Behavior differs on "
                "platforms/browsers."
            ),
        },
    )

    name = String(
        metadata={
            "label": "Name",
            "description": (
                "ZIM name. Used as identifier and filename (date will be appended)"
            ),
            "placeholder": "topic_eng",
        },
        required=True,
    )

    title = String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. Based on selection otherwise",
        },
        validate=validate_zim_title,
    )

    description = String(
        metadata={
            "label": "Description",
            "description": (
                "Custom description for your ZIM. Based on selection otherwise"
            ),
        },
        validate=validate_zim_description,
    )

    long_description = LongString(
        metadata={
            "label": "Long description",
            "description": (
                "Custom long description for your ZIM. Based on selection otherwise"
            ),
        },
        data_key="long-description",
        validate=validate_zim_longdescription,
    )

    creator = String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Defaults to TED",
        }
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        }
    )

    tags = String(
        metadata={
            "label": "ZIM Tags",
            "description": (
                "List of comma-separated Tags for the ZIM file. category:ted, ted, and"
                " _videos:yes added automatically"
            ),
        }
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

    output = String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file(s). Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
    )

    tmp_dir = String(
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

    zim_file = String(
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

    locale = String(
        metadata={
            "label": "Locale",
            "description": "The locale to use for the translations in ZIM",
        },
        data_key="locale",
    )
