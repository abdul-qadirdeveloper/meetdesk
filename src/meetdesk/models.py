from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class Status(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Meeting:
    """A meeting whose start and end are timezone-aware UTC datetimes; end is exclusive."""

    id: int
    title: str
    start: datetime
    end: datetime
    timezone: str
    organizer: str
    attendees: frozenset[str]
    room: str
    status: Status

    def __post_init__(self) -> None:
        for name, value in (("start", self.start), ("end", self.end)):
            if value.utcoffset() != timedelta(0):
                raise ValueError(f"{name} must be a timezone-aware UTC datetime")
        if self.end <= self.start:
            raise ValueError("end must be after start")

    @property
    def duration_min(self) -> int:
        return (self.end - self.start) // timedelta(minutes=1)
