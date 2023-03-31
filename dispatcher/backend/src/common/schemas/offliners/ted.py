from marshmallow import ValidationError, fields, validate, validates_schema

from common.schemas import SerializableSchema, StringEnum
from common.schemas.fields import validate_output, validate_zim_filename


class TedFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    indiv_zims = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Individual ZIM mode",
            "description": "Whether to produce one ZIM per topic/playlist",
        },
        data_key="indiv-zims",
    )

    topics = fields.String(
        metadata={
            "label": "Topics",
            "description": (
                "Comma-seperated list of topics to scrape; as given on ted.com/talks. "
                "Pass all for all topics"
            ),
        },
    )

    playlists = fields.String(
        metadata={
            "label": "TED Playlists",
            "description": (
                "Comma-seperated list of TED playlist IDs to scrape. Pass all for all "
                "playlists"
            ),
        },
    )

    languages = fields.String(
        metadata={
            "label": "Languages",
            "description": "Comma-seperated list of languages to filter videos",
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
    )

    subtitles = fields.String(
        metadata={
            "label": "Subtitles Setting",
            "description": (
                "Language setting for subtitles. all: include all available subtitles, "
                "matching (default): only subtitles matching language(s), none: include"
                " no subtitle. Also accepts comma-seperated list of language(s)"
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

    name = fields.String(
        metadata={
            "label": "Name",
            "description": (
                "ZIM name. Used as identifier and filename (date will be appended)"
            ),
            "placeholder": "topic_eng",
        },
    )

    name_format = fields.String(
        metadata={
            "label": "Name Format",
            "description": (
                "Format for building individual --name argument. Use variable "
                "{identity} for playlist id or topic name"
            ),
            "placeholder": "{identity}_eng",
        },
        data_key="name-format",
    )

    title = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. Based on selection otherwise",
        }
    )

    title_format = fields.String(
        metadata={
            "label": "Title Format",
            "description": "Custom title format for individual ZIMs",
        },
        data_key="title-format",
    )

    description = fields.String(
        metadata={
            "label": "Description",
            "description": (
                "Custom description for your ZIM. Based on selection otherwise"
            ),
        }
    )

    description_format = fields.String(
        metadata={
            "label": "Description Format",
            "description": "Custom description format for individual ZIMs",
        },
        data_key="description-format",
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

    output = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file(s). Leave it as `/output`",
        },
        missing="/output",
        default="/output",
        validate=validate_output,
    )

    tmp_dir = fields.String(
        metadata={
            "label": "Temp folder",
            "description": (
                "Where to create temporay build folder. Leave it as `/output`"
            ),
        },
        missing="/output",
        default="/output",
        validate=validate_output,
        data_key="tmp-dir",
    )

    metadata_from = fields.String(
        metadata={
            "label": "Metadata JSON",
            "description": (
                "File path or URL to a JSON file holding custom metadata for individual"
                " playlists/topics"
            ),
        },
        data_key="metadata-from",
    )

    zim_file = fields.String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on ZIM name if not provided)",
        },
        data_key="zim-file",
        validate=validate_zim_filename,
    )

    zim_file_format = fields.String(
        metadata={
            "label": "ZIM filename format",
            "description": (
                "Format for building individual --zim-file argument for individual "
                "ZIMs. Uses --name-format otherwise"
            ),
        },
        data_key="zim-file-format",
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
        },
        data_key="locale",
    )

    @validates_schema
    def validate(self, data, **kwargs):
        if data.get("indiv_zims"):
            if not data.get("name_format"):
                raise ValidationError("name-format required in individual ZIMs mode")
        else:
            if not data.get("name"):
                raise ValidationError("name required in normal mode")
