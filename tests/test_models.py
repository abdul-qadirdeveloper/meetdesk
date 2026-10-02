from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from meetdesk.models import Meeting, Status


def _meeting(start: datetime, end: datetime) -> Meeting:
    return Meeting(
        id=1,
        title="Design Review",
        start=start,
        end=end,
        timezone="Asia/Karachi",
        organizer="ali@meetdesk.test",
        attendees=frozenset({"ali@meetdesk.test", "hina@meetdesk.test"}),
        room="Huddle",
        status=Status.CONFIRMED,
    )


def test_duration_is_whole_minutes_between_start_and_end() -> None:
    meeting = _meeting(
        datetime(2026, 9, 28, 5, 30, tzinfo=UTC),
        datetime(2026, 9, 28, 6, 15, tzinfo=UTC),
    )
    assert meeting.duration_min == 45


def test_meeting_rejects_naive_datetimes() -> None:
    with pytest.raises(ValueError, match="UTC"):
        _meeting(
            datetime(2026, 9, 28, 5, 30),  # noqa: DTZ001
            datetime(2026, 9, 28, 6, 30, tzinfo=UTC),
        )


def test_meeting_rejects_non_utc_datetimes() -> None:
    karachi = ZoneInfo("Asia/Karachi")
    with pytest.raises(ValueError, match="UTC"):
        _meeting(
            datetime(2026, 9, 28, 10, 30, tzinfo=karachi),
            datetime(2026, 9, 28, 11, 30, tzinfo=karachi),
        )


@pytest.mark.parametrize("end_minute", [30, 0])
def test_meeting_rejects_end_not_after_start(end_minute: int) -> None:
    with pytest.raises(ValueError, match="after start"):
        _meeting(
            datetime(2026, 9, 28, 5, 30, tzinfo=UTC),
            datetime(2026, 9, 28, 5, end_minute, tzinfo=UTC),
        )
