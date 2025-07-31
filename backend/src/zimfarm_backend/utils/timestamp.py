import datetime

from sqlalchemy import BigInteger, cast, func, literal_column, select
from sqlalchemy.orm import InstrumentedAttribute

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


def get_status_timestamp_expr(
    jsonb_column: InstrumentedAttribute[list[tuple[str, datetime.datetime]]],
    status: str,
):
    elem = func.jsonb_array_elements(jsonb_column).alias("elem")
    return cast(
        # select the second element and then the date
        select(
            literal_column(
                "elem->1->>'$date'"
            )  # pyright: ignore[reportUnknownArgumentType]
        )
        .select_from(elem)
        .where(literal_column("elem->>0") == status)
        .limit(1)
        .scalar_subquery(),
        BigInteger,
    )
