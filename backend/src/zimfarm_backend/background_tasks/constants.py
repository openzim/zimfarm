import datetime

from humanfriendly import parse_timespan

from zimfarm_backend.common.constants import getenv, parse_bool

# History cleanup
HISTORY_TASK_PER_SCHEDULE = int(getenv("HISTORY_TASK_PER_SCHEDULE", default=10))

# Stalled task timeouts
STALLED_GONE_TIMEOUT = parse_timespan(getenv("STALLED_GONE_IMEOUT", default="1h"))
# when launching worker, it sets status to `started` then start scraper and
# change status to `scraper_started` so it's a minutes max duration
STALLED_STARTED_TIMEOUT = parse_timespan(
    getenv("STALLED_STARTED_TIMEOUT", default="30m")
)
# reserving a task is the lock that happens just before starting a worker
# thus changing its status to `started` quickly afterwards
STALLED_RESERVED_TIMEOUT = parse_timespan(
    getenv("STALLED_RESERVED_TIMEOUT", default="30m")
)
# only uploads happens after scraper_completed
STALLED_COMPLETED_TIMEOUT = parse_timespan(
    getenv("STALLED_COMPLETED_TIMEOUT", default="1d")
)
# cancel_request are picked-up during polls and may take a few minutes
# to be effective and reported
STALLED_CANCELREQ_TIMEOUT = parse_timespan(
    getenv("STALLED_CANCELREQ_TIMEOUT", default="30m")
)

# Old task deletion
# tasks older than this are removed
OLD_TASK_DELETION_THRESHOLD = datetime.timedelta(
    seconds=parse_timespan(getenv("TASKS_OLDER_THAN", default="10d"))
)
# flag to determine whether to remove old tasks
OLD_TASK_DELETION_ENABLED = parse_bool(
    getenv("SHOULD_REMOVE_OLD_TASKS", default="false")
)

# Periodic task names
PERIODIC_TASK_NAME = "periodic-tasks"

# Background task execution intervals (can be overridden via environment variables)
BACKGROUND_TASKS_SLEEP_DURATION = parse_timespan(
    getenv("BACKGROUND_TASKS_SLEEP_DURATION", default="1m")
)

# Task-specific intervals
REMOVE_OLD_TASKS_INTERVAL = datetime.timedelta(
    seconds=parse_timespan(getenv("REMOVE_OLD_TASKS_INTERVAL", default="10m"))
)
CANCEL_INCOMPLETE_TASKS_INTERVAL = datetime.timedelta(
    seconds=parse_timespan(getenv("CANCEL_INCOMPLETE_TASKS_INTERVAL", default="10m"))
)
CANCEL_STALE_TASKS_INTERVAL = datetime.timedelta(
    seconds=parse_timespan(getenv("CANCEL_STALE_TASKS_INTERVAL", default="10m"))
)
HISTORY_CLEANUP_INTERVAL = datetime.timedelta(
    seconds=parse_timespan(getenv("HISTORY_CLEANUP_INTERVAL", default="10m"))
)
REQUEST_TASKS_INTERVAL = datetime.timedelta(
    seconds=parse_timespan(getenv("REQUEST_TASKS_INTERVAL", default="1h"))
)
CMS_NOTIFICATIONS_INTERVAL = datetime.timedelta(
    seconds=parse_timespan(getenv("CMS_NOTIFICATIONS_INTERVAL", default="10m"))
)
CMS_MAXIMUM_RETRY_INTERVAL = parse_timespan(
    getenv("CMS_MAXIMUM_RETRY_INTERVAL", default="24h")
)
DELETE_ORPHANED_BLOBS_INTERVAL = datetime.timedelta(
    seconds=parse_timespan(getenv("DELETE_ORPHANED_BLOBS_INTERVAL", default="24h"))
)

CMS_OAUTH_ISSUER = getenv("CMS_OAUTH_ISSUER", default="https://login.kiwix.org")
CMS_OAUTH_CLIENT_ID = getenv("CMS_OAUTH_CLIENT_ID", default="")
CMS_OAUTH_CLIENT_SECRET = getenv("CMS_OAUTH_CLIENT_SECRET", default="")
CMS_OAUTH_AUDIENCE_ID = getenv("CMS_OAUTH_AUDIENCE_ID", default="")
# Number of seconds before the access token expires at which it should be renewed
CMS_TOKEN_RENEWAL_WINDOW = datetime.timedelta(
    seconds=parse_timespan(getenv("CMS_TOKEN_RENEWAL_WINDOW", default="5m"))
)
