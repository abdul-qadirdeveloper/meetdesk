import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from meetdesk.web import app, create_app

FIXTURES = Path(__file__).parent / "fixtures"

ALI = "ali@meetdesk.test"
SARA = "sara@meetdesk.test"
OMAR = "omar@meetdesk.test"
ZAIN = "zain@meetdesk.test"


@pytest.fixture
def client() -> TestClient:
    """A client for the default app, which serves data/sample_meetings.csv."""
    return TestClient(app)


def _ids(client: TestClient, url: str) -> list[int]:
    response = client.get(url)
    assert response.status_code == 200
    return [meeting["id"] for meeting in response.json()]


def test_meetings_on_a_date_returns_that_days_meetings(client: TestClient) -> None:
    assert _ids(client, "/meetings?date=2026-09-28") == [1, 2, 3, 4, 5, 6, 7, 8]


def test_meetings_without_a_date_returns_every_meeting(client: TestClient) -> None:
    assert _ids(client, "/meetings") == list(range(1, 41))


def test_meetings_on_a_date_with_no_meetings_is_empty(client: TestClient) -> None:
    assert _ids(client, "/meetings?date=2026-10-03") == []


def test_meetings_date_is_matched_against_the_utc_start() -> None:
    # 02:00 on the 29th in Asia/Karachi is 21:00 UTC on the 28th.
    client = TestClient(create_app(FIXTURES / "late_night_meeting.csv"))
    assert _ids(client, "/meetings?date=2026-09-28") == [1]
    assert _ids(client, "/meetings?date=2026-09-29") == []


def test_malformed_date_is_rejected(client: TestClient) -> None:
    assert client.get("/meetings?date=28-09-2026").status_code == 422


def test_meeting_by_id_returns_utc_times_and_sorted_attendees(
    client: TestClient,
) -> None:
    response = client.get("/meetings/6")
    assert response.status_code == 200
    assert response.json() == {
        "id": 6,
        "title": "UK Client Sync",
        "start": "2026-09-28T10:00:00Z",  # Europe/London 11:00
        "end": "2026-09-28T10:45:00Z",
        "duration_min": 45,
        "timezone": "Europe/London",
        "organizer": SARA,
        "attendees": [SARA, ZAIN],
        "room": "Studio",
        "status": "confirmed",
    }


def test_cancelled_meeting_is_still_returned_by_id(client: TestClient) -> None:
    assert client.get("/meetings/13").json()["status"] == "cancelled"


def test_unknown_meeting_id_is_not_found(client: TestClient) -> None:
    response = client.get("/meetings/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "no meeting with id 999"}


def test_non_integer_meeting_id_is_rejected(client: TestClient) -> None:
    assert client.get("/meetings/abc").status_code == 422


def test_conflicts_lists_the_three_sample_week_conflicts(client: TestClient) -> None:
    response = client.get("/conflicts")
    assert response.status_code == 200
    assert response.json() == [
        {"first_id": 4, "second_id": 5, "attendees": [ALI], "room": None},
        {"first_id": 21, "second_id": 22, "attendees": [SARA], "room": None},
        {"first_id": 31, "second_id": 32, "attendees": [OMAR], "room": None},
    ]


def test_csv_edits_show_up_without_restarting_the_app(tmp_path: Path) -> None:
    csv_path = tmp_path / "meetings.csv"
    shutil.copy(FIXTURES / "six_meetings.csv", csv_path)
    client = TestClient(create_app(csv_path))
    assert _ids(client, "/meetings") == [1, 2, 3, 4, 5, 6]
    assert len(client.get("/conflicts").json()) == 2

    shutil.copy(FIXTURES / "late_night_meeting.csv", csv_path)

    assert _ids(client, "/meetings") == [1]
    assert client.get("/meetings/1").json()["title"] == "Late deploy"
    assert client.get("/meetings/2").status_code == 404
    assert client.get("/conflicts").json() == []


def test_invalid_csv_is_reported_with_its_line_number() -> None:
    client = TestClient(create_app(FIXTURES / "bad_start.csv"))
    response = client.get("/meetings")
    assert response.status_code == 500
    assert "line 3" in response.json()["detail"]
    assert "start_local" in response.json()["detail"]
