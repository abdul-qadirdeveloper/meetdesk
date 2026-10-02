from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest

from meetdesk.importer import load_meetings
from meetdesk.models import Meeting, Status
from meetdesk.slots import FreeSlot, find_free_slots

FIXTURES = Path(__file__).parent / "fixtures"

ALI = "ali@meetdesk.test"
SARA = "sara@meetdesk.test"
OMAR = "omar@meetdesk.test"

KARACHI = ZoneInfo("Asia/Karachi")
MONDAY = date(2026, 9, 28)
TUESDAY = date(2026, 9, 29)
INDEPENDENCE_DAY = date(2026, 8, 14)

KARACHI_HOURS = ("Asia/Karachi", "09:00", "17:00")
LONDON_HOURS = ("Europe/London", "09:00", "17:00")
NEW_YORK_HOURS = ("America/New_York", "09:00", "17:00")

MakeMeeting = Callable[..., Meeting]


def pkt(hour: int, minute: int = 0, day: int = 28) -> datetime:
    """An Asia/Karachi local time in September 2026."""
    return datetime(2026, 9, day, hour, minute, tzinfo=KARACHI)


def test_sample_monday_free_slots_for_ali_and_sara(
    sample_meetings: list[Meeting],
) -> None:
    hours = {ALI: KARACHI_HOURS, SARA: KARACHI_HOURS}
    assert find_free_slots(sample_meetings, [ALI, SARA], MONDAY, 30, hours) == [
        FreeSlot(pkt(9, 30), pkt(10)),
        FreeSlot(pkt(11, 30), pkt(13)),
        FreeSlot(pkt(14, 30), pkt(15)),
        FreeSlot(pkt(15, 45), pkt(16, 45)),
    ]


def test_longer_duration_drops_short_gaps(sample_meetings: list[Meeting]) -> None:
    hours = {ALI: KARACHI_HOURS, SARA: KARACHI_HOURS}
    assert find_free_slots(sample_meetings, [ALI, SARA], MONDAY, 60, hours) == [
        FreeSlot(pkt(11, 30), pkt(13)),
        FreeSlot(pkt(15, 45), pkt(16, 45)),
    ]


def test_working_hours_in_another_timezone_narrow_the_window(
    sample_meetings: list[Meeting],
) -> None:
    hours = {ALI: KARACHI_HOURS, SARA: LONDON_HOURS}
    assert find_free_slots(sample_meetings, [ALI, SARA], MONDAY, 30, hours) == [
        FreeSlot(pkt(14, 30), pkt(15)),
        FreeSlot(pkt(15, 45), pkt(16, 45)),
    ]


def test_six_meetings_fixture_free_after_merged_busy_block() -> None:
    meetings = load_meetings(FIXTURES / "six_meetings.csv")
    hours = {ALI: KARACHI_HOURS, OMAR: KARACHI_HOURS}
    assert find_free_slots(meetings, [ALI, OMAR], MONDAY, 30, hours) == [
        FreeSlot(pkt(10, 40), pkt(17)),
    ]


def test_ali_and_sara_in_karachi_are_free_from_end_of_combined_busy_block() -> None:
    # Busy 09:00-09:15 (1), 09:10-10:00 (2), 10:00-10:30 (3) combine to 09:00-10:30.
    meetings = load_meetings(FIXTURES / "six_meetings.csv")
    hours = {ALI: KARACHI_HOURS, SARA: KARACHI_HOURS}
    assert find_free_slots(meetings, [ALI, SARA], MONDAY, 30, hours) == [
        FreeSlot(pkt(10, 30), pkt(17)),
    ]


def test_london_colleague_limits_shared_hours_to_karachi_afternoon() -> None:
    # London is on summer time (UTC+1) on 28 Sep: 09:00-17:00 there is 13:00-21:00 PKT.
    meetings = load_meetings(FIXTURES / "six_meetings.csv")
    hours = {ALI: KARACHI_HOURS, SARA: LONDON_HOURS}
    assert find_free_slots(meetings, [ALI, SARA], MONDAY, 30, hours) == [
        FreeSlot(pkt(13), pkt(17)),
    ]


def test_no_meetings_gives_whole_working_day() -> None:
    assert find_free_slots([], [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(9), pkt(17)),
    ]


def test_meeting_splits_the_working_day(make_meeting: MakeMeeting) -> None:
    meetings = [make_meeting(1, "05:00", 60, attendees=[ALI])]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(9), pkt(10)),
        FreeSlot(pkt(11), pkt(17)),
    ]


def test_back_to_back_meetings_leave_no_gap_between_them(
    make_meeting: MakeMeeting,
) -> None:
    meetings = [
        make_meeting(1, "04:00", 60, attendees=[ALI]),
        make_meeting(2, "05:00", 60, attendees=[ALI]),
    ]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(11), pkt(17)),
    ]


def test_gap_exactly_as_long_as_duration_is_free(make_meeting: MakeMeeting) -> None:
    meetings = [
        make_meeting(1, "04:00", 60, attendees=[ALI]),
        make_meeting(2, "05:30", 390, attendees=[ALI]),
    ]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(10), pkt(10, 30)),
    ]


def test_overlapping_meetings_are_merged_into_one_busy_block(
    make_meeting: MakeMeeting,
) -> None:
    meetings = [
        make_meeting(1, "05:00", 60, attendees=[ALI]),
        make_meeting(2, "05:30", 60, attendees=[ALI]),
    ]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(9), pkt(10)),
        FreeSlot(pkt(11, 30), pkt(17)),
    ]


def test_meeting_straddling_start_of_working_hours_is_clipped(
    make_meeting: MakeMeeting,
) -> None:
    meetings = [make_meeting(1, "03:30", 60, attendees=[ALI])]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(9, 30), pkt(17)),
    ]


def test_cancelled_meeting_does_not_block_time(make_meeting: MakeMeeting) -> None:
    meetings = [make_meeting(1, "05:00", 60, attendees=[ALI], status=Status.CANCELLED)]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(9), pkt(17)),
    ]


def test_meetings_of_other_people_do_not_block_time(make_meeting: MakeMeeting) -> None:
    meetings = [make_meeting(1, "05:00", 60, attendees=[SARA])]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(9), pkt(17)),
    ]


def test_meeting_organised_by_attendee_blocks_time(make_meeting: MakeMeeting) -> None:
    meetings = [replace(make_meeting(1, "05:00", 60, attendees=[SARA]), organizer=ALI)]
    assert find_free_slots(meetings, [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(pkt(9), pkt(10)),
        FreeSlot(pkt(11), pkt(17)),
    ]


def test_no_shared_working_hours_gives_no_slots() -> None:
    hours = {ALI: KARACHI_HOURS, SARA: NEW_YORK_HOURS}
    assert find_free_slots([], [ALI, SARA], MONDAY, 30, hours) == []


def test_slot_can_end_on_the_next_karachi_date() -> None:
    assert find_free_slots([], [SARA], TUESDAY, 30, {SARA: NEW_YORK_HOURS}) == [
        FreeSlot(pkt(18, day=29), pkt(2, day=30)),
    ]


def test_working_hours_crossing_utc_midnight_are_clipped_to_the_utc_day() -> None:
    hours = {OMAR: ("Asia/Tokyo", "06:00", "14:00")}
    assert find_free_slots([], [OMAR], TUESDAY, 30, hours) == [
        FreeSlot(pkt(5, day=29), pkt(10, day=29)),
        FreeSlot(pkt(2, day=30), pkt(5, day=30)),
    ]


def test_slots_are_in_karachi_local_time() -> None:
    (slot,) = find_free_slots([], [SARA], MONDAY, 30, {SARA: LONDON_HOURS})
    assert slot.start.utcoffset() == timedelta(hours=5)
    assert slot.end.utcoffset() == timedelta(hours=5)
    assert (slot.start.hour, slot.end.hour) == (13, 21)


def test_attendee_emails_are_matched_case_insensitively(
    make_meeting: MakeMeeting,
) -> None:
    meetings = [make_meeting(1, "05:00", 60, attendees=[ALI])]
    hours = {" Ali@MeetDesk.test": KARACHI_HOURS}
    assert find_free_slots(meetings, ["ALI@meetdesk.test "], MONDAY, 30, hours) == [
        FreeSlot(pkt(9), pkt(10)),
        FreeSlot(pkt(11), pkt(17)),
    ]


def test_holiday_gives_no_slots() -> None:
    # 14 Aug 2026 (Pakistan's Independence Day) is outside the usual test week on purpose.
    assert (
        find_free_slots(
            [], [ALI], INDEPENDENCE_DAY, 30, {ALI: KARACHI_HOURS}, {INDEPENDENCE_DAY}
        )
        == []
    )


def test_same_day_without_holidays_gives_whole_working_day() -> None:
    assert find_free_slots([], [ALI], INDEPENDENCE_DAY, 30, {ALI: KARACHI_HOURS}) == [
        FreeSlot(
            datetime(2026, 8, 14, 9, tzinfo=KARACHI),
            datetime(2026, 8, 14, 17, tzinfo=KARACHI),
        ),
    ]


def test_holiday_on_another_day_does_not_block_time() -> None:
    assert find_free_slots(
        [], [ALI], MONDAY, 30, {ALI: KARACHI_HOURS}, {INDEPENDENCE_DAY}
    ) == [
        FreeSlot(pkt(9), pkt(17)),
    ]


def test_invalid_arguments_still_raise_on_a_holiday() -> None:
    with pytest.raises(ValueError, match=SARA):
        find_free_slots([], [ALI, SARA], MONDAY, 30, {ALI: KARACHI_HOURS}, {MONDAY})


def test_attendee_without_working_hours_raises() -> None:
    with pytest.raises(ValueError, match=SARA):
        find_free_slots([], [ALI, SARA], MONDAY, 30, {ALI: KARACHI_HOURS})


@pytest.mark.parametrize("duration_min", [0, -30])
def test_non_positive_duration_raises(duration_min: int) -> None:
    with pytest.raises(ValueError, match="duration_min"):
        find_free_slots([], [ALI], MONDAY, duration_min, {ALI: KARACHI_HOURS})


def test_no_attendees_raises() -> None:
    with pytest.raises(ValueError, match="attendees"):
        find_free_slots([], [], MONDAY, 30, {ALI: KARACHI_HOURS})


def test_malformed_working_hours_raises() -> None:
    hours = {ALI: ("Asia/Karachi", "9am", "17:00")}
    with pytest.raises(ValueError):
        find_free_slots([], [ALI], MONDAY, 30, hours)


@pytest.mark.parametrize("closes", ["09:00", "08:00"])
def test_working_hours_ending_before_start_raises(closes: str) -> None:
    hours = {ALI: ("Asia/Karachi", "09:00", closes)}
    with pytest.raises(ValueError, match="working hours"):
        find_free_slots([], [ALI], MONDAY, 30, hours)


def test_unknown_working_hours_timezone_raises() -> None:
    hours = {ALI: ("Asia/Lahore", "09:00", "17:00")}
    with pytest.raises(ZoneInfoNotFoundError):
        find_free_slots([], [ALI], MONDAY, 30, hours)
