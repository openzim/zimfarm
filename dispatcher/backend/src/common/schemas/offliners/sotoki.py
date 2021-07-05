from marshmallow import fields, validate

from common.schemas import SerializableSchema
from common.schemas.fields import validate_output


class SotokiFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    domain = fields.String(
        metadata={
            "label": "Domain",
            "description": "Domain name from StackExchange to scrape.",
        },
        required=True,
    )

    name = fields.String(
        metadata={
            "label": "Name",
            "description": "ZIM name. Used as identifier and filename "
            "(date will be appended). Constructed from domain if not supplied",
        },
    )

    title = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. Site name otherwise",
        },
    )

    description = fields.String(
        metadata={
            "label": "Title",
            "description": "Custom description for your ZIM. Site tagline otherwise",
        },
    )

    favicon = fields.Url(
        metadata={
            "label": "Favicon",
            "description": "URL for Favicon. Site square logo otherwise",
        }
    )

    creator = fields.String(
        metadata={
            "label": "Creator",
            "description": "Name of content creator. “Stack Exchange” otherwise",
        },
    )

    publisher = fields.String(
        metadata={
            "label": "Creator",
            "description": "Custom publisher name (ZIM metadata). “OpenZIM” otherwise",
        },
    )

    tags = fields.String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of comma-separated Tags for the ZIM file. "
            "category:stack_exchange and stack_exchange added automatically",
        }
    )

    without_images = fields.Boolean(
        metadata={
            "label": "Without Images",
            "description": "Don't include images (in-post images, user icons). Faster.",
        },
        data_key="without-images",
    )

    without_user_profiles = fields.Boolean(
        metadata={
            "label": "Without User Profiles",
            "description": "Don't include user profile pages. Faster",
        },
        data_key="without-user-profiles",
    )

    without_user_identicons = fields.Boolean(
        metadata={
            "label": "Without Identicons",
            "description": "Don't include user's profile pictures. "
            "Replaced by generated ones. Faster",
        },
        data_key="without-user-identicons",
    )

    without_external_links = fields.Boolean(
        metadata={
            "label": "Without External links",
            "description": "Remove all external links from posts and user profiles. "
            "Link text is kept but not the address. Slower",
        },
        data_key="without-external-links",
    )

    without_unanswered = fields.Boolean(
        metadata={
            "label": "Without Unanswered",
            "description": "Don't include posts that have zero answer. Faster",
        },
        data_key="without-unanswered",
    )

    without_users_links = fields.Boolean(
        metadata={
            "label": "Without Users Links",
            "description": "Remove “user links” completely. Remove both url and text "
            "for a selected list of “social” websites. Slower",
        },
        data_key="without-users-links",
    )

    without_names = fields.Boolean(
        metadata={
            "label": "Without Names",
            "description": "Replace usernames in posts with generated ones",
        },
        data_key="without-names",
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

    threads = fields.Integer(
        metadata={
            "label": "Threads",
            "description": "Number of threads to use to handle tasks concurrently. "
            "Increase to speed-up I/O operations (disk, network). Default: 1",
        }
    )

    tmp_dir = fields.String(
        metadata={
            "label": "Temp folder",
            "placeholder": "/output",
            "description": "Where to create temporay build folder. "
            "Leave it as `/output`",
        },
        missing="/output",
        default="/output",
        validate=validate_output,
        data_key="tmp-dir",
    )

    zim_file = fields.String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM file name (based on --name if not provided). "
            "Include {period} to insert date period dynamically",
        },
        data_key="zim-file",
    )

    optimization_cache = fields.Url(
        metadata={
            "label": "Optimization Cache URL",
            "description": "S3 Storage URL including credentials and bucket",
            "secret": True,
        },
        data_key="optimization-cache",
    )

    mirror = fields.Url(
        metadata={
            "label": "Mirror",
            "description": "URL from which to download compressed XML dumps",
        },
    )

    stats_filename = fields.String(
        metadata={
            "label": "Stats filename",
            "placeholder": "/output/task_progress.json",
            "description": "Scraping progress file. "
            "Leave it as `/output/task_progress.json`",
        },
        data_key="statsFilename",
        missing="/output/task_progress.json",
        default="/output/task_progress.json",
        validate=validate.Equal("/output/task_progress.json"),
    )

    redis_url = fields.String(
        metadata={
            "label": "Redis URL",
            "description": "Redis URL to use as database. "
            "Keep it as unix:///var/run/redis.sock",
        },
        missing="unix:///var/run/redis.sock",
        default="unix:///var/run/redis.sock",
        validate=validate.Equal("unix:///var/run/redis.sock"),
        data_key="redis-url",
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )
