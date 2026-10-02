from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from meetdesk.models import Meeting, Status
from meetdesk.timeutil import local_to_utc

OUTPUT_TIMEZONE = "Asia/Karachi"

Interval = tuple[datetime, datetime]


@dataclass(frozen=True)
class FreeSlot:
    """A free interval; start and end are aware Asia/Karachi datetimes, end exclusive."""

    start: datetime
    end: datetime


def find_free_slots(
    meetings: Iterable[Meeting],
    attendees: Iterable[str],
    day: date,
    duration_min: int,
    working_hours: Mapping[str, tuple[str, str, str]],
    holidays: Collection[date] = frozenset(),
) -> list[FreeSlot]:
    """Return the intervals on a UTC day when every attendee is free, in Asia/Karachi time.

    working_hours maps each email to (IANA timezone, "HH:MM" start, "HH:MM" end). An
    interval is free when it lies inside every attendee's working hours and none of
    them has a non-cancelled meeting. Only intervals of at least duration_min minutes
    are returned, sorted by start.

    holidays is supplied by the caller; when day is one of them no slots are returned.

    Raises ValueError for a non-positive duration, no attendees, an attendee without
    working hours, or malformed working hours, and zoneinfo.ZoneInfoNotFoundError
    for an unknown timezone.
    """
    if duration_min <= 0:
        raise ValueError(f"duration_min must be positive, got {duration_min}")
    people = {_normalise_email(email) for email in attendees}
    if not people:
        raise ValueError("attendees is empty")
    hours = {_normalise_email(email): value for email, value in working_hours.items()}
    missing = sorted(people - hours.keys())
    if missing:
        raise ValueError(f"no working hours for {', '.join(missing)}")

    day_start = datetime.combine(day, time.min, tzinfo=UTC)
    available: list[Interval] = [(day_start, day_start + timedelta(days=1))]
    for email in sorted(people):
        available = _intersect(available, _working_windows(day, *hours[email]))
    if day in holidays:
        return []

    busy = [
        (meeting.start, meeting.end)
        for meeting in meetings
        if meeting.status is not Status.CANCELLED
        and (people & meeting.attendees or meeting.organizer in people)
    ]

    output = ZoneInfo(OUTPUT_TIMEZONE)
    return [
        FreeSlot(start.astimezone(output), end.astimezone(output))
        for start, end in _subtract(available, busy)
        if end - start >= timedelta(minutes=duration_min)
    ]


def _working_windows(
    day: date, timezone: str, opens: str, closes: str
) -> list[Interval]:
    """Working hours as UTC intervals for the local dates around a UTC day."""
    windows: list[Interval] = []
    for offset in (-1, 0, 1):
        local_day = (day + timedelta(days=offset)).isoformat()
        start = local_to_utc(f"{local_day} {opens}", timezone)
        end = local_to_utc(f"{local_day} {closes}", timezone)
        if end <= start:
            raise ValueError(
                f"working hours must end after they start: {opens}-{closes}"
            )
        windows.append((start, end))
    return windows


def _intersect(first: list[Interval], second: list[Interval]) -> list[Interval]:
    overlaps = [
        (max(first_start, second_start), min(first_end, second_end))
        for first_start, first_end in first
        for second_start, second_end in second
    ]
    return sorted((start, end) for start, end in overlaps if start < end)


def _subtract(available: list[Interval], busy: list[Interval]) -> list[Interval]:
    """Remove busy intervals from available ones; busy may overlap and be unsorted."""
    blocks = sorted(busy)
    free: list[Interval] = []
    for start, end in available:
        cursor = start
        for busy_start, busy_end in blocks:
            if busy_start >= end:
                break
            if busy_start > cursor:
                free.append((cursor, busy_start))
            cursor = max(cursor, busy_end)
        if cursor < end:
            free.append((cursor, end))
    return free


def _normalise_email(email: str) -> str:
    return email.strip().lower()
