from collections.abc import Iterable
from dataclasses import dataclass

from meetdesk.models import Meeting, Status


@dataclass(frozen=True)
class Conflict:
    """Two overlapping meetings (first_id < second_id) and what they share."""

    first_id: int
    second_id: int
    attendees: frozenset[str]
    room: str | None


def find_conflicts(meetings: Iterable[Meeting]) -> list[Conflict]:
    """Return one Conflict per pair of overlapping meetings sharing an attendee or a room.

    Cancelled meetings are ignored. A meeting's end is exclusive, so back-to-back
    meetings do not conflict. The result is sorted by (first_id, second_id).
    """
    active = sorted(
        (meeting for meeting in meetings if meeting.status is not Status.CANCELLED),
        key=lambda meeting: meeting.start,
    )
    conflicts: list[Conflict] = []
    for index, earlier in enumerate(active):
        # Sorted by start: once a neighbour starts at or after this meeting's end,
        # no later one can overlap it either.
        for position in range(index + 1, len(active)):
            later = active[position]
            if later.start >= earlier.end:
                break
            attendees = earlier.attendees & later.attendees
            room = earlier.room if earlier.room and earlier.room == later.room else None
            if attendees or room is not None:
                first_id, second_id = sorted((earlier.id, later.id))
                conflicts.append(Conflict(first_id, second_id, attendees, room))
    return sorted(
        conflicts, key=lambda conflict: (conflict.first_id, conflict.second_id)
    )
