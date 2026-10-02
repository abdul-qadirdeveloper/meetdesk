from datetime import UTC, datetime
from pathlib import Path

import pytest

from meetdesk.importer import MeetingImportError, load_meetings
from meetdesk.models import Meeting, Status

FIXTURES = Path(__file__).parent / "fixtures"


def _by_id(meetings: list[Meeting]) -> dict[int, Meeting]:
    return {meeting.id: meeting for meeting in meetings}


def test_sample_file_loads_forty_meetings(sample_meetings: list[Meeting]) -> None:
    assert [meeting.id for meeting in sample_meetings] == list(range(1, 41))


@pytest.mark.parametrize(
    ("meeting_id", "expected"),
    [
        (1, datetime(2026, 9, 28, 4, 0, tzinfo=UTC)),  # Asia/Karachi 09:00
        (6, datetime(2026, 9, 28, 10, 0, tzinfo=UTC)),  # Europe/London 11:00
        (16, datetime(2026, 9, 29, 13, 0, tzinfo=UTC)),  # America/New_York 09:00
    ],
)
def test_local_start_is_converted_to_utc(
    sample_meetings: list[Meeting], meeting_id: int, expected: datetime
) -> None:
    assert _by_id(sample_meetings)[meeting_id].start == expected


def test_end_is_start_plus_duration(sample_meetings: list[Meeting]) -> None:
    sprint_planning = _by_id(sample_meetings)[2]
    assert sprint_planning.start == datetime(2026, 9, 28, 5, 0, tzinfo=UTC)
    assert sprint_planning.end == datetime(2026, 9, 28, 6, 30, tzinfo=UTC)
    assert sprint_planning.duration_min == 90


def test_attendees_are_split_on_semicolons(sample_meetings: list[Meeting]) -> None:
    sprint_planning = _by_id(sample_meetings)[2]
    assert sprint_planning.organizer == "sara@meetdesk.test"
    assert sprint_planning.attendees == {
        "sara@meetdesk.test",
        "omar@meetdesk.test",
        "zain@meetdesk.test",
    }


def test_cancelled_rows_are_loaded_with_cancelled_status(
    sample_meetings: list[Meeting],
) -> None:
    cancelled = [m.id for m in sample_meetings if m.status is Status.CANCELLED]
    assert cancelled == [13, 24, 37]


def test_emails_are_lowercased_and_trimmed() -> None:
    (meeting,) = load_meetings(FIXTURES / "mixed_case_emails.csv")
    assert meeting.organizer == "ali@meetdesk.test"
    assert meeting.attendees == {"ali@meetdesk.test", "hina@meetdesk.test"}


def test_missing_timezone_raises_with_line_number() -> None:
    with pytest.raises(MeetingImportError, match="timezone") as excinfo:
        load_meetings(FIXTURES / "missing_timezone.csv")
    assert excinfo.value.line == 3
    assert "line 3" in str(excinfo.value)


def test_unknown_timezone_raises() -> None:
    with pytest.raises(MeetingImportError, match="timezone.*PKT") as excinfo:
        load_meetings(FIXTURES / "unknown_timezone.csv")
    assert excinfo.value.line == 3


def test_malformed_start_raises() -> None:
    with pytest.raises(MeetingImportError, match="start_local") as excinfo:
        load_meetings(FIXTURES / "bad_start.csv")
    assert excinfo.value.line == 3


def test_zero_duration_raises() -> None:
    with pytest.raises(MeetingImportError, match="duration_min") as excinfo:
        load_meetings(FIXTURES / "zero_duration.csv")
    assert excinfo.value.line == 3


def test_non_integer_duration_raises() -> None:
    with pytest.raises(MeetingImportError, match="duration_min") as excinfo:
        load_meetings(FIXTURES / "bad_duration.csv")
    assert excinfo.value.line == 3


def test_duplicate_id_raises() -> None:
    with pytest.raises(MeetingImportError, match="duplicate id 1") as excinfo:
        load_meetings(FIXTURES / "duplicate_ids.csv")
    assert excinfo.value.line == 3


def test_unknown_status_raises() -> None:
    with pytest.raises(MeetingImportError, match="status.*tentative") as excinfo:
        load_meetings(FIXTURES / "bad_status.csv")
    assert excinfo.value.line == 3


def test_missing_column_raises() -> None:
    with pytest.raises(MeetingImportError, match="timezone") as excinfo:
        load_meetings(FIXTURES / "missing_column.csv")
    assert excinfo.value.line == 1
