from marshmallow import fields, validate

from common.schemas import SerializableSchema, StringEnum, HexColor
from common.schemas.fields import validate_output


class YoutubeFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    kind = StringEnum(
        metadata={
            "label": "Type",
            "description": "Type of collection. Only `playlist` accepts multiple IDs.",
        },
        validate=validate.OneOf(["channel", "playlist", "user"]),
        data_key="type",
        required=True,
    )
    ident = fields.String(
        metadata={
            "label": "Youtube ID",
            "description": "Youtube ID of the collection. Seperate multiple playlists with commas.",
        },
        data_key="id",
        required=True,
    )
    api_key = fields.String(
        metadata={"label": "API Key", "description": "Youtube API Token"},
        data_key="api-key",
        required=True,
    )

    name = fields.String(
        metadata={
            "label": "ZIM Name",
            "description": "Used as identifier and filename (date will be appended)",
            "placeholder": "mychannel_eng_all",
        },
        required=True,
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
    concurrency = fields.Integer(
        metadata={
            "label": "Concurrency",
            "description": "Number of concurrent threads to use",
        },
    )

    all_subtitles = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "All Subtitles",
            "description": "Include auto-generated subtitles",
        },
        data_key="all-subtitles",
    )
    pagination = fields.Integer(
        metadata={
            "label": "Pagination",
            "description": "Number of videos per page (40 otherwise)",
        },
    )
    autoplay = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Auto-play",
            "description": "Enable autoplay on video articles (home never have autoplay).",
        },
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
            "description": "ZIM file name (based on --name if not provided)",
        },
        data_key="zim-file",
    )
    language = fields.String(
        metadata={
            "label": "Language",
            "description": "ISO-639-3 (3 chars) language code of content",
        }
    )
    locale = fields.String(
        metadata={
            "label": "Locale",
            "description": "Locale name to use for translations (if avail) and time representations. Defaults to --language or English.",
        }
    )
    title = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom title for your project and ZIM. Default to Channel name (of first video if playlists)",
        }
    )
    description = fields.String(metadata={"label": "Description", "description": ""})
    creator = fields.String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Defaults to Channel name or “Youtue Channels”",
        }
    )
    tags = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of Tags for the ZIM file. _videos:yes added automatically",
        }
    )

    profile = fields.Url(
        metadata={
            "label": "Profile Image",
            "description": "Custom profile image. Squared. Will be resized to 100x100px",
        }
    )
    banner = fields.Url(
        metadata={
            "label": "Banner Image",
            "description": "Custom banner image. Will be resized to 1060x175px",
        }
    )
    main_color = HexColor(
        metadata={
            "label": "Main Color",
            "description": "Custom color. Hex/HTML syntax (#DEDEDE). Default to main color of profile image.",
        },
        data_key="main-color",
    )
    secondary_color = HexColor(
        metadata={
            "label": "Secondary Color",
            "description": "Custom secondary color. Hex/HTML syntax (#DEDEDE). Default to secondary color of profile image.",
        },
        data_key="secondary-color",
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )
