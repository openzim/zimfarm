from marshmallow import ValidationError, fields, validate, validates_schema

from common.schemas import HexColor, SerializableSchema, String, StringEnum
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
)


class YoutubeFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    indiv_playlists = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Playlists mode",
            "description": "Build one ZIM per playlist of the channel or user",
        },
        data_key="indiv-playlists",
    )

    kind = StringEnum(
        metadata={
            "label": "Type",
            "description": "Type of collection. Only `playlist` accepts multiple IDs.",
        },
        validate=validate.OneOf(["channel", "playlist", "user"]),
        data_key="type",
        required=True,
    )
    ident = String(
        metadata={
            "label": "Youtube ID",
            "description": "Youtube ID of the collection. "
            "Separate multiple playlists with commas.",
        },
        data_key="id",
        required=True,
    )
    api_key = String(
        metadata={"label": "API Key", "description": "Youtube API Token"},
        data_key="api-key",
        required=True,
    )

    name = String(
        metadata={
            "label": "ZIM Name",
            "description": "Used as identifier and filename (date will be appended)",
            "placeholder": "mychannel_eng_all",
        },
    )
    playlists_name = String(
        metadata={
            "label": "Playlists name",
            "description": "Format for building individual --name argument. "
            "Required in playlist mode. Variables: {title}, {description}, "
            "{playlist_id}, {slug} (from title), {creator_id}, {creator_name}",
        },
        data_key="playlists-name",
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

    dateafter = String(
        metadata={
            "label": "Only after date",
            "description": "Custom filter to download videos uploaded on "
            "or after specified date. Format: YYYYMMDD or "
            "(now|today)[+-][0-9](day|week|month|year)(s)?",
        }
    )

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": "S3 Storage URL including credentials and bucket",
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
            "placeholder": "/output",
            "description": "Where to create temporay build folder. "
            "Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
        data_key="tmp-dir",
    )

    zim_file = String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided). "
            "Include {period} to insert date period dynamically",
        },
        data_key="zim-file",
        validate=validate_zim_filename,
    )
    playlists_zim_file = String(
        metadata={
            "label": "Playlists ZIM filename",
            "description": "Format for building individual --zim-file argument. "
            "Uses --playlists-name otherwise",
        },
        data_key="playlists-zim-file",
    )

    language = String(
        metadata={
            "label": "Language",
            "description": "ISO-639-3 (3 chars) language code of content",
        }
    )
    locale = String(
        metadata={
            "label": "Locale",
            "description": "Locale name to use for translations (if avail) "
            "and time representations. Defaults to --language or English.",
        }
    )

    title = String(
        metadata={
            "label": "Title",
            "description": "Custom title for your project and ZIM. Default to "
            "Channel name (of first video if playlists)",
        }
    )
    playlists_title = String(
        metadata={
            "label": "Playlists title",
            "description": "Custom title format for individual playlist ZIM",
        },
        data_key="playlists-title",
    )

    description = String(
        metadata={"label": "Description", "description": "Description for ZIM"},
        validate=validate_zim_description,
    )
    playlists_description = String(
        metadata={
            "label": "Playlists description",
            "description": "Custom description format for individual playlist ZIM",
        },
        data_key="playlists-description",
    )

    creator = String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Defaults to Channel name "
            "or “Youtue Channels”",
        }
    )
    tags = String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of Tags for the ZIM file. "
            "_videos:yes added automatically",
        }
    )

    metadata_from = String(
        metadata={
            "label": "Metadata JSON",
            "description": "File path or URL to a JSON file holding custom metadata "
            "for individual playlists",
        },
        data_key="metadata-from",
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

    @validates_schema
    def validate(self, data, **kwargs):
        if data.get("indiv_playlists"):
            if not data.get("playlists_name"):
                raise ValidationError("playlists-name required in playlists mode")
        else:
            if not data.get("name"):
                raise ValidationError("name required in normal mode")
