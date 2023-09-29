from marshmallow import fields

from common.schemas import LongString, SerializableSchema, String
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
    validate_zim_longdescription,
)


class KolibriFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    channel_id = String(
        metadata={
            "label": "Channel ID",
            "description": "The Kolibri channel ID that you want to scrape",
        },
        data_key="channel-id",
        required=True,
    )

    root_id = String(
        metadata={
            "label": "Root ID",
            "description": "The node ID (usually Topic) from where to start "
            "the scraper. Defaults to the root of the channel.",
        },
        data_key="root-id",
    )

    name = String(
        metadata={
            "label": "Name",
            "description": "ZIM name. Used as identifier "
            "and filename (date will be appended)",
        },
        required=True,
    )

    title = String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. Kolibri channel name otherwise",
        }
    )

    description = String(
        metadata={
            "label": "Description",
            "description": "Custom description for your ZIM. "
            "Kolibri channel description otherwise",
        },
        validate=validate_zim_description,
    )

    long_description = LongString(
        metadata={
            "label": "Long description",
            "description": "Custom long description for your ZIM. "
            "If not provided, either not set or Kolibri channel description if it was "
            "too long to fit entirely in ZIM description",
        },
        data_key="long-description",
        validate=validate_zim_longdescription,
    )

    favicon = fields.Url(
        metadata={
            "label": "Favicon",
            "description": "URL for Favicon. Kolibri channel thumbnail otherwise "
            "or default Kolobri logo if missing",
        },
        required=False,
    )

    css = fields.Url(
        metadata={
            "label": "Custom CSS",
            "description": "URL to a single CSS file to be included in all pages "
            "(but not on kolibri-html-content ones). "
            "Inlude external resources using data URL.",
        },
        required=False,
    )

    about = fields.Url(
        metadata={
            "label": "Custom About",
            "description": "URL to a single HTML file to use as an about page. "
            "Place everythong inside `body .container` "
            "(including stylesheets and scripts) "
            "as only this and your <title> will be merged into the actual about page. "
            "Remember to include images inline using data URL.",
        },
        required=False,
    )

    creator = String(
        metadata={
            "label": "Content Creator",
            "description": "Name of content creator. Kolibri "
            "channel author or “Kolibri” otherwise",
        }
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “OpenZIM” otherwise",
        }
    )

    tags = String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of comma-separated Tags for the ZIM file. "
            "category:other, kolibri, and _videos:yes added automatically",
        }
    )

    use_webm = fields.Boolean(
        metadata={
            "label": "Use WebM",
            "description": "Kolibri videos are in mp4. Choosing webm will require "
            "videos to be re-encoded. Result will be slightly smaller and of lower "
            "quality. WebM support is bundled in the ZIM so videos "
            "will be playable on every platform.",
        },
        data_key="use-webm",
        truthy=[True],
        falsy=[False],
    )

    low_quality = fields.Boolean(
        metadata={
            "label": "Low quality",
            "description": "Uses only the `low_res` version of videos if available. "
            "If not, recompresses using agressive compression.",
        },
        data_key="low-quality",
        truthy=[True],
        falsy=[False],
    )

    autoplay = fields.Boolean(
        metadata={
            "label": "Autoplay",
            "description": "Enable autoplay on video and audio articles. "
            "Behavior differs on platforms/browsers.",
        },
        truthy=[True],
        falsy=[False],
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

    threads = fields.Integer(
        metadata={
            "label": "Threads",
            "description": "Number of threads to use to handle nodes concurrently. "
            "Increase to speed-up I/O operations (disk, network). Default: 1",
        }
    )

    processes = fields.Integer(
        metadata={
            "label": "Processes",
            "description": "Number of processes to dedicate to media optimizations. "
            "Default: 1",
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

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )
