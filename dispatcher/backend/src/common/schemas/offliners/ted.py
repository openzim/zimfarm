from marshmallow import fields, validate

from common.schemas import SerializableSchema, StringEnum
from common.schemas.fields import validate_output


class TedFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    topics = fields.String(
        metadata={
            "label": "Topics",
            "description": "Comma-seperated list of topics to scrape; as given on ted.com/talks",
        },
    )

    playlist = fields.String(
        metadata={
            "label": "TED Playlist",
            "description": "A playlist ID from ted.com/playlists to scrape videos from",
        },
    )

    languages = fields.String(
        metadata={
            "label": "Languages",
            "description": "Comma-seperated list of languages to filter videos",
        }
    )

    subtitles_enough = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Subtitles enough?",
            "description": "Whether to include videos that have a subtitle in requested language(s) if audio is in another language",
        },
    )

    subtitles = fields.String(
        metadata={
            "label": "Subtitles Setting",
            "description": "Language setting for subtitles. all: include all available subtitles, matching (default): only subtitles matching language(s), none: include no subtitle. Also accepts comma-seperated list of language(s)",
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
            "description": "Enable autoplay on video articles. Behavior differs on platforms/browsers.",
        },
    )

    name = fields.String(
        metadata={
            "label": "Name",
            "description": "ZIM name. Used as identifier and filename (date will be appended)",
            "placeholder": "topic_eng",
        },
        required=True,
    )

    title = fields.String(
        metadata={
            "label": "Title",
            "description": "ustom title for your ZIM. Based on selection otherwise",
        }
    )
    description = fields.String(
        metadata={
            "label": "Description",
            "description": "Custom description for your ZIM. Based on selection otherwise",
        }
    )
    creator = fields.String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Defaults to TED",
        }
    )
    tags = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of comma-separated Tags for the ZIM file. category:ted, ted, and _videos:yes added automatically",
        }
    )

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": "URL with credentials and bucket name to S3 Optimization Cache",
            "secret": True,
        },
        data_key="optimization-cache",
    )

    use_any_optimized_version = fields.Boolean(
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
            "description": "Output folder for ZIM file or build folder. Leave it as `/output`",
        },
        missing="/output",
        default="/output",
        validate=validate_output,
    )

    zim_file = fields.String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on ZIM name if not provided)",
        },
        data_key="zim-file",
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )

    max_videos_per_topic = fields.Integer(
        metadata={
            "label": "Max Videos per Topic",
            "description": "Max number of videos to scrape in each topic. Default behaviour is to scrape all",
        },
    )
