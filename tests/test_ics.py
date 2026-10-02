from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from meetdesk.ics import export_ics
from meetdesk.models import Meeting, Status

ALI = "ali@meetdesk.test"
SARA = "sara@meetdesk.test"
OMAR = "omar@meetdesk.test"

GENERATED_AT = datetime(2026, 9, 28, 6, 0, tzinfo=UTC)

MakeMeeting = Callable[..., Meeting]


def _lines(ics: str) -> list[str]:
    return ics.split("\r\n")


def test_sample_week_exports_one_event_per_confirmed_meeting(
    sample_meetings: list[Meeting],
) -> None:
    lines = _lines(export_ics(sample_meetings, generated_at=GENERATED_AT))
    assert lines.count("BEGIN:VEVENT") == 37
    assert lines.count("END:VEVENT") == 37


def test_sample_week_excludes_cancelled_meetings(
    sample_meetings: list[Meeting],
) -> None:
    lines = _lines(export_ics(sample_meetings, generated_at=GENERATED_AT))
    for cancelled_id in (13, 24, 37):
        assert f"UID:meeting-{cancelled_id}@meetdesk" not in lines
    assert "SUMMARY:Customer Demo Rehearsal" not in lines
    assert "UID:meeting-12@meetdesk" in lines


def test_cancelled_meeting_is_not_exported(make_meeting: MakeMeeting) -> None:
    confirmed = make_meeting(1, "09:00")
    cancelled = make_meeting(2, "10:00", status=Status.CANCELLED)
    lines = _lines(export_ics([confirmed, cancelled], generated_at=GENERATED_AT))
    assert [line for line in lines if line.startswith("UID:")] == [
        "UID:meeting-1@meetdesk"
    ]


def test_event_start_and_end_are_utc_with_z_suffix(
    sample_meetings: list[Meeting],
) -> None:
    # Meeting 1 is 09:00 for 30 minutes in Asia/Karachi (UTC+5).
    kickoff = [meeting for meeting in sample_meetings if meeting.id == 1]
    lines = _lines(export_ics(kickoff, generated_at=GENERATED_AT))
    assert "DTSTART:20260928T040000Z" in lines
    assert "DTEND:20260928T043000Z" in lines


def test_event_lists_every_property_in_order(make_meeting: MakeMeeting) -> None:
    meeting = make_meeting(7, "09:00", 45, attendees=[SARA, ALI, OMAR], room="Studio")
    assert export_ics([meeting], generated_at=GENERATED_AT) == (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//MeetDesk//MeetDesk 0.1//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:meeting-7@meetdesk\r\n"
        "DTSTAMP:20260928T060000Z\r\n"
        "DTSTART:20260928T090000Z\r\n"
        "DTEND:20260928T094500Z\r\n"
        "SUMMARY:Meeting 7\r\n"
        "LOCATION:Studio\r\n"
        "ATTENDEE:mailto:ali@meetdesk.test\r\n"
        "ATTENDEE:mailto:omar@meetdesk.test\r\n"
        "ATTENDEE:mailto:sara@meetdesk.test\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def test_events_keep_the_order_of_the_input(make_meeting: MakeMeeting) -> None:
    meetings = [make_meeting(5, "11:00"), make_meeting(2, "09:00")]
    lines = _lines(export_ics(meetings, generated_at=GENERATED_AT))
    assert [line for line in lines if line.startswith("UID:")] == [
        "UID:meeting-5@meetdesk",
        "UID:meeting-2@meetdesk",
    ]


def test_meeting_without_a_room_has_no_location(make_meeting: MakeMeeting) -> None:
    lines = _lines(
        export_ics([make_meeting(1, "09:00", room="")], generated_at=GENERATED_AT)
    )
    assert not [line for line in lines if line.startswith("LOCATION")]


def test_commas_semicolons_and_backslashes_in_text_are_escaped(
    make_meeting: MakeMeeting,
) -> None:
    meeting = replace(
        make_meeting(1, "09:00", room="Floor 2, East"),
        title="Budget; Q4\\Q1\nfinal",
    )
    lines = _lines(export_ics([meeting], generated_at=GENERATED_AT))
    assert "SUMMARY:Budget\\; Q4\\\\Q1\\nfinal" in lines
    assert "LOCATION:Floor 2\\, East" in lines


def test_long_lines_are_folded_at_75_octets(make_meeting: MakeMeeting) -> None:
    title = "Quarterly planning " * 10
    meeting = replace(make_meeting(1, "09:00"), title=title)
    lines = _lines(export_ics([meeting], generated_at=GENERATED_AT))
    assert max(len(line.encode("utf-8")) for line in lines) == 75
    # Unfolding (dropping each CRLF + space) gives back the original line.
    start = lines.index("DTEND:20260928T100000Z") + 1
    end = lines.index("LOCATION:Board")
    folded = lines[start:end]
    assert len(folded) == 3
    assert all(line.startswith(" ") for line in folded[1:])
    assert folded[0] + "".join(line[1:] for line in folded[1:]) == f"SUMMARY:{title}"


def test_folding_never_splits_a_multibyte_character(
    make_meeting: MakeMeeting,
) -> None:
    title = "é" * 100
    meeting = replace(make_meeting(1, "09:00"), title=title)
    ics = export_ics([meeting], generated_at=GENERATED_AT)
    lines = _lines(ics)
    assert max(len(line.encode("utf-8")) for line in lines) <= 75
    assert f"SUMMARY:{title}" in ics.replace("\r\n ", "")


def test_no_meetings_gives_a_calendar_with_no_events() -> None:
    assert export_ics([], generated_at=GENERATED_AT) == (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//MeetDesk//MeetDesk 0.1//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "END:VCALENDAR\r\n"
    )


def test_naive_generated_at_is_rejected(make_meeting: MakeMeeting) -> None:
    naive = GENERATED_AT.replace(tzinfo=None)
    with pytest.raises(ValueError, match="timezone-aware"):
        export_ics([make_meeting(1, "09:00")], generated_at=naive)
