import csv
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfoNotFoundError

from meetdesk.models import Meeting, Status
from meetdesk.timeutil import local_to_utc

COLUMNS = (
    "id",
    "title",
    "start_local",
    "duration_min",
    "timezone",
    "organizer",
    "attendees",
    "room",
    "status",
)


class MeetingImportError(ValueError):
    """A problem in a meetings CSV, with the 1-based line number it was found on."""

    def __init__(self, line: int, message: str) -> None:
        super().__init__(f"line {line}: {message}")
        self.line = line


def load_meetings(path: Path) -> list[Meeting]:
    """Load a meetings CSV into Meeting objects, in file order.

    Raises MeetingImportError on the first invalid row.
    """
    meetings: list[Meeting] = []
    seen_ids: set[int] = set()
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing = [name for name in COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            raise MeetingImportError(1, f"missing column(s): {', '.join(missing)}")
        for row in reader:
            line = reader.line_num
            meeting = _parse_row(row, line)
            if meeting.id in seen_ids:
                raise MeetingImportError(line, f"duplicate id {meeting.id}")
            seen_ids.add(meeting.id)
            meetings.append(meeting)
    return meetings


def _parse_row(row: dict[str, str | None], line: int) -> Meeting:
    values = {name: (row[name] or "").strip() for name in COLUMNS}

    try:
        meeting_id = int(values["id"])
    except ValueError:
        raise MeetingImportError(
            line, f"id {values['id']!r} is not an integer"
        ) from None

    try:
        duration_min = int(values["duration_min"])
    except ValueError:
        raise MeetingImportError(
            line, f"duration_min {values['duration_min']!r} is not a whole number"
        ) from None
    if duration_min <= 0:
        raise MeetingImportError(
            line, f"duration_min must be positive, got {duration_min}"
        )

    timezone = values["timezone"]
    if not timezone:
        raise MeetingImportError(line, "timezone is missing")
    try:
        start = local_to_utc(values["start_local"], timezone)
    except ZoneInfoNotFoundError:
        raise MeetingImportError(line, f"unknown timezone {timezone!r}") from None
    except ValueError:
        raise MeetingImportError(
            line, f"start_local {values['start_local']!r} is not YYYY-MM-DD HH:MM"
        ) from None

    try:
        status = Status(values["status"])
    except ValueError:
        raise MeetingImportError(line, f"unknown status {values['status']!r}") from None

    attendees = frozenset(
        email
        for part in values["attendees"].split(";")
        if (email := _normalise_email(part))
    )
    if not attendees:
        raise MeetingImportError(line, "attendees is empty")

    return Meeting(
        id=meeting_id,
        title=values["title"],
        start=start,
        end=start + timedelta(minutes=duration_min),
        timezone=timezone,
        organizer=_normalise_email(values["organizer"]),
        attendees=attendees,
        room=values["room"],
        status=status,
    )


def _normalise_email(email: str) -> str:
    return email.strip().lower()
