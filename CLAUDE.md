# MeetDesk
Meetings management app: import meetings, detect double-bookings, find free slots, export .ics.

## Commands
- Test: `uv run pytest -q`
- Lint/format: `uv run ruff check --fix . && uv run ruff format .`
- Types: `uv run mypy src`

## Rules
- Domain code lives in `src/meetdesk/`, one module per concern (models, importer, scheduler, slots, ics, web).
- Store every datetime as a timezone-aware UTC `datetime`. Convert with `zoneinfo`, never `pytz`, never naive datetimes.
- Durations are whole minutes (`int`).
- A meeting's end is exclusive: a meeting ending 10:00 does not overlap one starting 10:00.
- Every new public function gets type hints and a pytest test in `tests/test_<module>.py`.
- IMPORTANT: Never change a test's expected values to make it pass. Fix the code instead.

@.claude/conventions/testing.md