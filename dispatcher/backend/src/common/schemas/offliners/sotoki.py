from marshmallow import fields, validate

from common.schemas import SerializableSchema, String
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_filename,
)


class SotokiFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    domain = String(
        metadata={
            "label": "Domain",
            "description": "Domain name from StackExchange to scrape.",
        },
        required=True,
    )

    name = String(
        metadata={
            "label": "Name",
            "description": "ZIM name. Used as identifier and filename "
            "(date will be appended). Constructed from domain if not supplied",
        },
    )

    title = String(
        metadata={
            "label": "Title",
            "description": "Custom title for your ZIM. Site name otherwise",
        },
    )

    description = String(
        metadata={
            "label": "Description",
            "description": "Custom description for your ZIM. Site tagline otherwise",
        },
        validate=validate_zim_description,
    )

    favicon = fields.Url(
        metadata={
            "label": "Favicon",
            "description": "URL for Favicon. Site square logo otherwise",
        }
    )

    creator = String(
        metadata={
            "label": "Creator",
            "description": "Name of content creator. “Stack Exchange” otherwise",
        },
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        },
    )

    tag = String(
        metadata={
            "label": "ZIM Tag",
            "description": "Single additional tag for the ZIM file. Scraper generic "
            "flags (category:stack_exchange, stack_exchange, ... are always added "
            "automatically)",
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

    censor_words_list = fields.Url(
        metadata={
            "label": "Words black list",
            "description": "URL to a text file "
            "containing one word per line. Each of them to be removed from all content."
            " Very slow.",
        },
        data_key="censor-words-list",
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

    threads = fields.Integer(
        metadata={
            "label": "Threads",
            "description": "Number of threads to use to handle tasks concurrently. "
            "Increase to speed-up I/O operations (disk, network). Default: 1",
        }
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

    stats_filename = String(
        metadata={
            "label": "Stats filename",
            "placeholder": "/output/task_progress.json",
            "description": "Scraping progress file. "
            "Leave it as `/output/task_progress.json`",
        },
        data_key="stats-filename",
        load_default="/output/task_progress.json",
        dump_default="/output/task_progress.json",
        validate=validate.Equal("/output/task_progress.json"),
    )

    redis_url = String(
        metadata={
            "label": "Redis URL",
            "description": "Redis URL to use as database. "
            "Keep it as unix:///var/run/redis.sock",
        },
        load_default="unix:///var/run/redis.sock",
        dump_default="unix:///var/run/redis.sock",
        validate=validate.Equal("unix:///var/run/redis.sock"),
        data_key="redis-url",
    )

    defrag_redis = String(
        metadata={
            "label": "Defrag redis",
            "description": "Keep it as ENV:REDIS_PID",
        },
        load_default="ENV:REDIS_PID",
        dump_default="ENV:REDIS_PID",
        validate=validate.Equal("ENV:REDIS_PID"),
        data_key="defrag-redis",
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )

    keep_redis = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Keep redis",
            "description": "Don't flush redis DB on exit. Keep it enabled.",
        },
        load_default=True,
        dump_default=True,
        validate=validate.Equal(True),
        data_key="keep-redis",
    )
