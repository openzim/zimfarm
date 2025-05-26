from pydantic import Field
from pydantic.types import AnyUrl

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    S3OptimizationCache,
    ZIMDescription,
    ZIMFileName,
    ZIMOutputFolder,
    ZIMTitle,
)


class SotokiFlagsSchema(BaseModel):
    domain: NotEmptyString = Field(
        title="Domain",
        description="Domain name from StackExchange to scrape.",
    )

    name: NotEmptyString = Field(
        title="Name",
        description="ZIM name. Used as identifier and filename "
        "(date will be appended). Constructed from domain if not supplied",
    )

    title: ZIMTitle = Field(
        title="Title",
        description="Custom title for your ZIM. Site name otherwise",
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Custom description for your ZIM. Site tagline otherwise",
    )

    favicon: AnyUrl | None = Field(
        title="Favicon",
        description="URL for Favicon. Site square logo otherwise",
        default=None,
    )

    creator: NotEmptyString = Field(
        title="Creator",
        description="Name of content creator. “Stack Exchange” otherwise",
        default="Stack Exchange",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    tag: NotEmptyString = Field(
        title="ZIM Tag",
        description="Single additional tag for the ZIM file. Scraper generic "
        "flags (category:stack_exchange, stack_exchange, ... are always added "
        "automatically)",
    )

    without_images: bool = Field(
        title="Without Images",
        description="Don't include images (in-post images, user icons). Faster.",
        alias="without-images",
    )

    without_user_profiles: bool = Field(
        title="Without User Profiles",
        description="Don't include user profile pages. Faster",
        alias="without-user-profiles",
    )

    without_user_identicons: bool = Field(
        title="Without Identicons",
        description="Don't include user's profile pictures. "
        "Replaced by generated ones. Faster",
        alias="without-user-identicons",
    )

    without_external_links: bool = Field(
        title="Without External links",
        description="Remove all external links from posts and user profiles. "
        "Link text is kept but not the address. Slower",
        alias="without-external-links",
    )

    without_unanswered: bool = Field(
        title="Without Unanswered",
        description="Don't include posts that have zero answer. Faster",
        alias="without-unanswered",
    )

    without_users_links: bool = Field(
        title="Without Users Links",
        description="Remove “user links” completely. Remove both url and text "
        "for a selected list of “social” websites. Slower",
        alias="without-users-links",
    )

    without_names: bool = Field(
        title="Without Names",
        description="Replace usernames in posts with generated ones",
        alias="without-names",
    )

    censor_words_list: AnyUrl = Field(
        title="Words black list",
        description="URL to a text file "
        "containing one word per line. Each of them to be removed from all content."
        " Very slow.",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
        default="/output",
        validate_default=True,
    )

    threads: int = Field(
        title="Threads",
        description="Number of threads to use to handle tasks concurrently. "
        "Increase to speed-up I/O operations (disk, network). Default: 1",
        default=1,
    )

    tmp_dir: ZIMOutputFolder = Field(
        title="Temp folder",
        description="Where to create temporay build folder. Leave it as `/output`",
        default="/output",
        validate_default=True,
        alias="tmp-dir",
    )

    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Include {period} to insert date period dynamically",
        alias="zim-file",
    )

    optimization_cache: S3OptimizationCache = Field(
        title="Optimization Cache URL",
        description="S3 Storage URL including credentials and bucket",
        alias="optimization-cache",
    )

    mirror: AnyUrl = Field(
        title="Mirror",
        description="URL from which to download compressed XML dumps",
    )

    stats_filename: NotEmptyString = Field(
        title="Stats filename",
        description="Scraping progress file. Leave it as `/output/task_progress.json`",
        default="/output/task_progress.json",
        alias="stats-filename",
        pattern=r"^/output/task_progress\.json$",
    )

    redis_url: NotEmptyString = Field(
        title="Redis URL",
        description="Redis URL to use as database. "
        "Keep it as unix:///var/run/redis.sock",
        default="unix:///var/run/redis.sock",
        validate_default=True,
        alias="redis-url",
        pattern=r"^unix:///var/run/redis\.sock$",
    )

    defrag_redis: NotEmptyString = Field(
        title="Defrag redis",
        description="Keep it as ENV:REDIS_PID",
        default="ENV:REDIS_PID",
        validate_default=True,
        alias="defrag-redis",
        pattern=r"^ENV:REDIS_PID$",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )

    keep_redis: bool = Field(
        title="Keep redis",
        description="Don't flush redis DB on exit. Keep it enabled.",
        default=True,
        validate_default=True,
        alias="keep-redis",
    )
