from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfoNotFoundError

import pytest

from meetdesk.timeutil import local_to_utc


@pytest.mark.parametrize(
    ("local", "timezone", "expected"),
    [
        ("2026-09-28 09:00", "Asia/Karachi", datetime(2026, 9, 28, 4, 0, tzinfo=UTC)),
        ("2026-09-30 10:00", "Europe/London", datetime(2026, 9, 30, 9, 0, tzinfo=UTC)),
        (
            "2026-10-01 09:00",
            "America/New_York",
            datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
        ),
    ],
)
def test_local_time_is_converted_to_utc(
    local: str, timezone: str, expected: datetime
) -> None:
    assert local_to_utc(local, timezone) == expected


def test_result_is_timezone_aware_utc() -> None:
    result = local_to_utc("2026-09-28 09:00", "Asia/Karachi")
    assert result.utcoffset() == timedelta(0)


def test_conversion_can_cross_into_the_previous_utc_day() -> None:
    assert local_to_utc("2026-09-29 02:30", "Asia/Karachi") == datetime(
        2026, 9, 28, 21, 30, tzinfo=UTC
    )


def test_same_clock_time_in_different_timezones_gives_different_instants() -> None:
    karachi = local_to_utc("2026-09-30 10:00", "Asia/Karachi")
    london = local_to_utc("2026-09-30 10:00", "Europe/London")
    assert london - karachi == timedelta(hours=4)


@pytest.mark.parametrize(
    "local", ["2026-09-28", "28/09/2026 09:00", "2026-09-28 09:00:00", ""]
)
def test_malformed_local_string_raises_value_error(local: str) -> None:
    with pytest.raises(ValueError):
        local_to_utc(local, "Asia/Karachi")


def test_unknown_timezone_raises() -> None:
    with pytest.raises(ZoneInfoNotFoundError):
        local_to_utc("2026-09-28 09:00", "Asia/Lahore")
