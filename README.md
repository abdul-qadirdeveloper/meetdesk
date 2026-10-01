# MeetDesk

MeetDesk is a small Python library for working with meeting schedules. It is meant to:

- import meetings from a CSV file, converting each local start time to UTC using its IANA timezone;
- detect double-bookings, where an attendee is in two overlapping meetings;
- find free slots when a group of people are all available.

The project is at the scaffolding stage: the package and tooling are set up, but these features are not implemented yet.

## Sample data

`data/sample_meetings.csv` holds 40 meetings for the week of 28 Sep to 2 Oct 2026 across `Asia/Karachi`, `Europe/London` and `America/New_York`. It contains 3 double-bookings, 1 back-to-back pair that does not overlap, and 3 cancelled meetings.

Columns: `id`, `title`, `start_local` (`YYYY-MM-DD HH:MM`), `duration_min`, `timezone`, `organizer`, `attendees` (semicolon-separated emails), `room`, `status` (`confirmed` or `cancelled`).

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```
uv sync
```

## Running the tests

```
uv run pytest
```

Lint and type-check:

```
uv run ruff check .
uv run mypy src
```
