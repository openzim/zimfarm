from pydantic import AnyUrl, Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    OptionalNotEmptyString,
    OptionalS3OptimizationCache,
    OptionalZIMDescription,
    OptionalZIMFileName,
    OptionalZIMOutputFolder,
    OptionalZIMTitle,
)


class SotokiFlagsSchema(DashModel):
    domain: NotEmptyString = Field(
        title="Domain",
        description="Domain name from StackExchange to scrape.",
    )

    name: OptionalNotEmptyString = OptionalField(
        title="Name",
        description="ZIM name. Used as identifier and filename "
        "(date will be appended). Constructed from domain if not supplied",
    )

    title: OptionalZIMTitle = OptionalField(
        title="Title",
        description="Custom title for your ZIM. Site name otherwise",
    )

    description: OptionalZIMDescription = OptionalField(
        title="Description",
        description="Custom description for your ZIM. Site tagline otherwise",
    )

    favicon: AnyUrl | None = OptionalField(
        title="Favicon",
        description="URL for Favicon. Site square logo otherwise",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Creator",
        description='Name of content creator. "Stack Exchange" otherwise',
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description='Custom publisher name (ZIM metadata). "openZIM" otherwise',
    )

    tag: OptionalNotEmptyString = OptionalField(
        title="ZIM Tag",
        description="Single additional tag for the ZIM file. Scraper generic "
        "flags (category:stack_exchange, stack_exchange, ... are always added "
        "automatically)",
    )

    without_images: bool | None = OptionalField(
        title="Without Images",
        description="Don't include images (in-post images, user icons). Faster.",
    )

    without_user_profiles: bool | None = OptionalField(
        title="Without User Profiles",
        description="Don't include user profile pages. Faster",
    )

    without_user_identicons: bool | None = OptionalField(
        title="Without Identicons",
        description="Don't include user's profile pictures. "
        "Replaced by generated ones. Faster",
    )

    without_external_links: bool | None = OptionalField(
        title="Without External links",
        description="Remove all external links from posts and user profiles. "
        "Link text is kept but not the address. Slower",
    )

    without_unanswered: bool | None = OptionalField(
        title="Without Unanswered",
        description="Don't include posts that have zero answer. Faster",
    )

    without_users_links: bool | None = OptionalField(
        title="Without Users Links",
        description='Remove "user links" completely. Remove both url and text '
        'for a selected list of "social" websites. Slower',
    )

    without_names: bool | None = OptionalField(
        title="Without Names",
        description="Replace usernames in posts with generated ones",
    )

    censor_words_list: AnyUrl | None = OptionalField(
        title="Words black list",
        description="URL to a text file "
        "containing one word per line. Each of them to be removed from all content."
        " Very slow.",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
    )

    threads: int | None = OptionalField(
        title="Threads",
        description="Number of threads to use to handle tasks concurrently. "
        "Increase to speed-up I/O operations (disk, network). Default: 1",
        ge=1,
    )

    tmp_dir: OptionalZIMOutputFolder = OptionalField(
        title="Temp folder",
        description="Where to create temporay build folder. Leave it as `/output`",
    )

    zim_file: OptionalZIMFileName = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Include {period} to insert date period dynamically",
    )

    optimization_cache: OptionalS3OptimizationCache = OptionalField(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
    )

    mirror: AnyUrl | None = OptionalField(
        title="Mirror",
        description="URL from which to download compressed XML dumps",
    )

    stats_filename: OptionalNotEmptyString = OptionalField(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
    )

    redis_url: OptionalNotEmptyString = OptionalField(
        title="Redis URL",
        description="Redis URL to use as database. "
        "Keep it as unix:///var/run/redis.sock",
    )

    defrag_redis: OptionalNotEmptyString = OptionalField(
        title="Defrag redis",
        description="Keep it as ENV:REDIS_PID",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )

    keep_redis: bool | None = OptionalField(
        title="Keep redis",
        description="Don't flush redis DB on exit. Keep it enabled.",
    )
