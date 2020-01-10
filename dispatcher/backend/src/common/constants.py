import os
import datetime

OPENSSL_BIN = os.getenv("OPENSSL_BIN", "/usr/bin/openssl")
MESSAGE_VALIDITY = 60  # number of seconds before a message expire

REFRESH_TOKEN_EXPIRY = 180  # days
TOKEN_EXPIRY = 24  # hours

DEFAULT_SCHEDULE_DURATION = datetime.timedelta(days=31).total_seconds()
