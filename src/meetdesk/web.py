from datetime import date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from meetdesk.importer import MeetingImportError, load_meetings
from meetdesk.models import Meeting, Status
from meetdesk.scheduler import Conflict, find_conflicts

DEFAULT_CSV = Path(__file__).resolve().parents[2] / "data" / "sample_meetings.csv"


class MeetingOut(BaseModel):
    """A meeting as JSON; start and end are UTC, end is exclusive."""

    id: int
    title: str
    start: datetime
    end: datetime
    duration_min: int
    timezone: str
    organizer: str
    attendees: list[str]
    room: str
    status: Status


class ConflictOut(BaseModel):
    """Two overlapping meetings (first_id < second_id) and what they share."""

    first_id: int
    second_id: int
    attendees: list[str]
    room: str | None


def create_app(csv_path: Path = DEFAULT_CSV) -> FastAPI:
    """Build the MeetDesk API over a meetings CSV.

    The CSV is re-read on every request, so edits to it show up without a restart.
    """
    app = FastAPI(title="MeetDesk")

    @app.exception_handler(MeetingImportError)
    def invalid_csv(request: Request, error: MeetingImportError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(error)})

    @app.get("/meetings")
    def list_meetings(
        day: Annotated[
            date | None,
            Query(alias="date", description="UTC day, YYYY-MM-DD"),
        ] = None,
    ) -> list[MeetingOut]:
        """Return the meetings starting on a UTC day, or every meeting without one."""
        meetings = load_meetings(csv_path)
        if day is not None:
            meetings = [meeting for meeting in meetings if meeting.start.date() == day]
        return [_meeting_out(meeting) for meeting in meetings]

    @app.get("/meetings/{meeting_id}")
    def get_meeting(meeting_id: int) -> MeetingOut:
        for meeting in load_meetings(csv_path):
            if meeting.id == meeting_id:
                return _meeting_out(meeting)
        raise HTTPException(status_code=404, detail=f"no meeting with id {meeting_id}")

    @app.get("/conflicts")
    def list_conflicts() -> list[ConflictOut]:
        return [
            _conflict_out(conflict)
            for conflict in find_conflicts(load_meetings(csv_path))
        ]

    return app


def _meeting_out(meeting: Meeting) -> MeetingOut:
    return MeetingOut(
        id=meeting.id,
        title=meeting.title,
        start=meeting.start,
        end=meeting.end,
        duration_min=meeting.duration_min,
        timezone=meeting.timezone,
        organizer=meeting.organizer,
        attendees=sorted(meeting.attendees),
        room=meeting.room,
        status=meeting.status,
    )


def _conflict_out(conflict: Conflict) -> ConflictOut:
    return ConflictOut(
        first_id=conflict.first_id,
        second_id=conflict.second_id,
        attendees=sorted(conflict.attendees),
        room=conflict.room,
    )


app = create_app()
