import datetime

DEFAULT_TIMESTAMP = datetime.datetime(1970, 1, 1)


def get_timestamp_for_status(
    timestamp_list: list[tuple[str, datetime.datetime]],
    status: str,
    default: datetime.datetime = DEFAULT_TIMESTAMP,
) -> datetime.datetime:
    """Extract datetime from timestamp list for a given status."""
    # Filter timestamps for the given status and sort by timestamp (most recent first)
    matching_timestamps = [
        timestamp for status_str, timestamp in timestamp_list if status_str == status
    ]

    if not matching_timestamps:
        return default

    # Return the most recent timestamp for this status
    return max(matching_timestamps)
