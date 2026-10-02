from collections.abc import Callable
from pathlib import Path

from meetdesk.importer import load_meetings
from meetdesk.models import Meeting, Status
from meetdesk.scheduler import Conflict, find_conflicts

FIXTURES = Path(__file__).parent / "fixtures"

ALI = "ali@meetdesk.test"
SARA = "sara@meetdesk.test"
OMAR = "omar@meetdesk.test"

MakeMeeting = Callable[..., Meeting]


def _only(meetings: list[Meeting], *ids: int) -> list[Meeting]:
    return [meeting for meeting in meetings if meeting.id in ids]


def test_sample_week_has_exactly_three_conflicts(
    sample_meetings: list[Meeting],
) -> None:
    assert find_conflicts(sample_meetings) == [
        Conflict(4, 5, frozenset({ALI}), None),
        Conflict(21, 22, frozenset({SARA}), None),
        Conflict(31, 32, frozenset({OMAR}), None),
    ]


def test_back_to_back_meetings_do_not_conflict(sample_meetings: list[Meeting]) -> None:
    assert find_conflicts(_only(sample_meetings, 10, 11)) == []


def test_same_clock_time_in_different_timezones_does_not_conflict(
    sample_meetings: list[Meeting],
) -> None:
    assert find_conflicts(_only(sample_meetings, 18, 21)) == []


def test_overlapping_meetings_with_nothing_shared_do_not_conflict(
    sample_meetings: list[Meeting],
) -> None:
    assert find_conflicts(_only(sample_meetings, 18, 19)) == []


def test_six_meetings_fixture_has_exactly_two_conflicts() -> None:
    meetings = load_meetings(FIXTURES / "six_meetings.csv")
    assert find_conflicts(meetings) == [
        Conflict(1, 2, frozenset({SARA}), None),
        Conflict(3, 6, frozenset({OMAR}), None),
    ]


def test_cancelled_meeting_never_conflicts(make_meeting: MakeMeeting) -> None:
    confirmed = make_meeting(1, "09:00", attendees=[ALI], room="Board")
    cancelled = make_meeting(
        2, "09:30", attendees=[ALI], room="Board", status=Status.CANCELLED
    )
    assert find_conflicts([confirmed, cancelled]) == []


def test_overlapping_meetings_in_same_room_conflict_on_room(
    make_meeting: MakeMeeting,
) -> None:
    first = make_meeting(1, "09:00", attendees=[ALI], room="Board")
    second = make_meeting(2, "09:30", attendees=[SARA], room="Board")
    assert find_conflicts([first, second]) == [Conflict(1, 2, frozenset(), "Board")]


def test_back_to_back_meetings_in_same_room_do_not_conflict(
    make_meeting: MakeMeeting,
) -> None:
    first = make_meeting(1, "09:00", 60, attendees=[ALI], room="Board")
    second = make_meeting(2, "10:00", 60, attendees=[SARA], room="Board")
    assert find_conflicts([first, second]) == []


def test_pair_sharing_attendee_and_room_is_reported_once_with_both(
    make_meeting: MakeMeeting,
) -> None:
    first = make_meeting(1, "09:00", attendees=[ALI, SARA], room="Board")
    second = make_meeting(2, "09:30", attendees=[ALI, OMAR], room="Board")
    assert find_conflicts([first, second]) == [
        Conflict(1, 2, frozenset({ALI}), "Board")
    ]


def test_pair_sharing_two_attendees_lists_both(make_meeting: MakeMeeting) -> None:
    first = make_meeting(1, "09:00", attendees=[ALI, SARA], room="Board")
    second = make_meeting(2, "09:30", attendees=[ALI, SARA, OMAR], room="Studio")
    assert find_conflicts([first, second]) == [
        Conflict(1, 2, frozenset({ALI, SARA}), None)
    ]


def test_meeting_contained_in_another_conflicts(make_meeting: MakeMeeting) -> None:
    outer = make_meeting(1, "09:00", 120, attendees=[ALI], room="Board")
    inner = make_meeting(2, "09:30", 30, attendees=[ALI], room="Studio")
    assert find_conflicts([outer, inner]) == [Conflict(1, 2, frozenset({ALI}), None)]


def test_pair_is_reported_once_with_lower_id_first(make_meeting: MakeMeeting) -> None:
    later_id_starts_first = make_meeting(7, "09:00", attendees=[ALI], room="Board")
    earlier_id_starts_second = make_meeting(3, "09:30", attendees=[ALI], room="Studio")
    assert find_conflicts([later_id_starts_first, earlier_id_starts_second]) == [
        Conflict(3, 7, frozenset({ALI}), None)
    ]


def test_no_meetings_gives_no_conflicts() -> None:
    assert find_conflicts([]) == []
