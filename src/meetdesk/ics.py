from collections.abc import Iterable
from datetime import UTC, datetime

from meetdesk.models import Meeting, Status

PRODID = "-//MeetDesk//MeetDesk 0.1//EN"
MAX_LINE_OCTETS = 75


def export_ics(
    meetings: Iterable[Meeting], *, generated_at: datetime | None = None
) -> str:
    """Return an iCalendar (RFC 5545) document with one VEVENT per confirmed meeting.

    Cancelled meetings are left out and events keep the order of ``meetings``.
    DTSTART and DTEND are UTC with a Z suffix. ``generated_at`` becomes every
    event's DTSTAMP and defaults to the current time. Lines end in CRLF, so write
    the result with ``newline=""`` to stop the platform translating them.
    """
    if generated_at is None:
        generated_at = datetime.now(UTC)
    elif generated_at.utcoffset() is None:
        raise ValueError("generated_at must be a timezone-aware datetime")
    stamp = _utc_stamp(generated_at)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
    ]
    for meeting in meetings:
        if meeting.status is not Status.CONFIRMED:
            continue
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:meeting-{meeting.id}@meetdesk")
        lines.append(f"DTSTAMP:{stamp}")
        lines.append(f"DTSTART:{_utc_stamp(meeting.start)}")
        lines.append(f"DTEND:{_utc_stamp(meeting.end)}")
        lines.append(f"SUMMARY:{_escape_text(meeting.title)}")
        if meeting.room:
            lines.append(f"LOCATION:{_escape_text(meeting.room)}")
        # attendees is a frozenset: sort so the output is the same on every run.
        lines.extend(f"ATTENDEE:mailto:{email}" for email in sorted(meeting.attendees))
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "".join(f"{_fold(line)}\r\n" for line in lines)


def _utc_stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _escape_text(value: str) -> str:
    """Escape a TEXT property value (RFC 5545 section 3.3.11)."""
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def _fold(line: str) -> str:
    """Fold a content line so no physical line is longer than 75 octets.

    Continuation lines start with a space, which counts towards their 75 octets.
    A multi-byte UTF-8 character is never split across lines.
    """
    chunks: list[str] = []
    current = ""
    size = 0
    for char in line:
        width = len(char.encode("utf-8"))
        if size + width > MAX_LINE_OCTETS:
            chunks.append(current)
            current, size = " ", 1
        current += char
        size += width
    chunks.append(current)
    return "\r\n".join(chunks)
