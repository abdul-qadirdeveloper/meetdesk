from datetime import UTC, datetime
from zoneinfo import ZoneInfo

LOCAL_FORMAT = "%Y-%m-%d %H:%M"


def local_to_utc(local: str, timezone: str) -> datetime:
    """Convert a local "YYYY-MM-DD HH:MM" string in an IANA timezone to an aware UTC datetime.

    Raises ValueError if the string does not match the format, and
    zoneinfo.ZoneInfoNotFoundError if the timezone name is unknown.
    """
    aware = datetime.strptime(local, LOCAL_FORMAT).replace(tzinfo=ZoneInfo(timezone))
    return aware.astimezone(UTC)
