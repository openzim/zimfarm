from marshmallow import fields, validate

from common.schemas import HexColor, LongString, SerializableSchema, String, StringEnum
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
    validate_zim_longdescription,
)


class YoutubeFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": "Technical Flag: S3 Storage URL including credentials and "
            "bucket",
            "secret": True,
        },
        data_key="optimization-cache",
    )

    api_key = String(
        metadata={
            "label": "API Key",
            "description": "Technical flag: Youtube API Token",
            "secret": True,
        },
        data_key="api-key",
        required=True,
    )

    ident = String(
        metadata={
            "label": "Youtube ID(s)",
            "description": "Youtube ID(s) of the user, channel or playlist(s) to ZIM "
            "(depending on the Type chosen below). Only playlist Type support multiple "
            "Youtube IDs and they must be separated by commas.",
        },
        data_key="id",
        required=True,
    )

    kind = StringEnum(
        metadata={
            "label": "Type",
            "description": "Type of Youtube ID.",
        },
        validate=validate.OneOf(["channel", "playlist", "user"]),
        data_key="type",
        required=True,
    )

    language = String(
        metadata={
            "label": "Language",
            "description": "ISO-639-3 (3 chars) language code of content",
        }
    )

    name = String(
        metadata={
            "label": "ZIM Name",
            "description": "Used as identifier and filename (date will be appended)",
            "placeholder": "mychannel_eng_all",
        },
        required=True,
    )

    zim_file = String(
        metadata={
            "label": "ZIM Filename",
            "description": "ZIM file name (optional, based on ZIM Name "
            "if not provided). Include {period} to insert date period dynamically",
        },
        data_key="zim-file",
        validate=validate_zim_filename,
    )

    title = String(
        metadata={
            "label": "ZIM Title",
            "description": "Custom title for your ZIM. "
            "Default to Channel name (of first video if playlists)",
        }
    )

    description = String(
        metadata={
            "label": "ZIM Description",
            "description": "Description (up to 80 chars) for ZIM",
        },
        validate=validate_zim_description,
    )

    long_description = LongString(
        metadata={
            "label": "ZIM Long Description",
            "description": "Long description (up to 4000 chars) for ZIM",
        },
        data_key="long-description",
        validate=validate_zim_longdescription,
    )

    creator = String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Defaults to Channel name "
            "or “Youtube Channels”",
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
            "description": "List of Tags for the ZIM file. "
            "_videos:yes added automatically",
        }
    )

    locale = String(
        metadata={
            "label": "Locale",
            "description": "Locale name to use for translations (if avail) "
            "and time representations. Defaults to Language flag value or English if "
            "flag is not set.",
        }
    )

    dateafter = String(
        metadata={
            "label": "Only after date",
            "description": "Custom filter to download videos uploaded on "
            "or after specified date. Format: YYYYMMDD or "
            "(now|today)[+-][0-9](day|week|month|year)(s)?",
        }
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

    use_any_optimized_version = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Use any optimized version",
            "description": "Use the cached files if present, whatever the version",
        },
        data_key="use-any-optimized-version",
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
            "description": "Enable autoplay on video articles "
            "(home never have autoplay).",
        },
    )

    profile = fields.Url(
        metadata={
            "label": "Profile Image",
            "description": "Custom profile image. Squared. "
            "Will be resized to 100x100px",
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
            "description": "Custom color. Hex/HTML syntax (#DEDEDE). "
            "Default to main color of profile image.",
        },
        data_key="main-color",
    )

    secondary_color = HexColor(
        metadata={
            "label": "Secondary Color",
            "description": "Custom secondary color. Hex/HTML syntax (#DEDEDE). "
            "Default to secondary color of profile image.",
        },
        data_key="secondary-color",
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )

    concurrency = fields.Integer(
        metadata={
            "label": "Concurrency",
            "description": "Expert flag: Number of concurrent threads to use",
        },
    )

    output = String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Technical flag: Output folder for ZIM file(s). Leave it "
            "as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
    )

    tmp_dir = String(
        metadata={
            "label": "Temp folder",
            "placeholder": "/output",
            "description": "Technical flag: Where to create temporay build folder. "
            "Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
        data_key="tmp-dir",
    )
