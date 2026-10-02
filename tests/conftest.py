from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from meetdesk.importer import load_meetings
from meetdesk.models import Meeting, Status

SAMPLE_CSV = Path(__file__).parent.parent / "data" / "sample_meetings.csv"


@pytest.fixture
def sample_meetings() -> list[Meeting]:
    return load_meetings(SAMPLE_CSV)


@pytest.fixture
def make_meeting() -> Callable[..., Meeting]:
    """Build a Meeting on Monday 2026-09-28 from a UTC "HH:MM" start and a duration."""

    def _make(
        id: int,
        start: str,
        minutes: int = 60,
        *,
        attendees: Iterable[str] = ("ali@meetdesk.test",),
        room: str = "Board",
        status: Status = Status.CONFIRMED,
    ) -> Meeting:
        hour, minute = (int(part) for part in start.split(":"))
        begin = datetime(2026, 9, 28, hour, minute, tzinfo=UTC)
        people = frozenset(attendees)
        return Meeting(
            id=id,
            title=f"Meeting {id}",
            start=begin,
            end=begin + timedelta(minutes=minutes),
            timezone="UTC",
            organizer=min(people),
            attendees=people,
            room=room,
            status=status,
        )

    return _make
