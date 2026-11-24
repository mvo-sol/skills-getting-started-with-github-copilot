import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def test_activities():
    return {
        "Test Club": {
            "description": "Test activity",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["existing@example.edu"],
        },
        "Full Club": {
            "description": "Full activity",
            "schedule": "Mondays",
            "max_participants": 1,
            "participants": ["full@example.edu"],
        },
        "Crowded Club": {
            "description": "Activity at capacity",
            "schedule": "Wednesdays",
            "max_participants": 2,
            "participants": ["one@example.edu", "two@example.edu"],
        },
    }


@pytest.fixture
def client(monkeypatch, test_activities):
    monkeypatch.setattr(app_module, "activities", test_activities)
    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_available_activities(client, test_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == test_activities


def test_signup_adds_participant(client, test_activities):
    response = client.post(
        "/activities/Test%20Club/signup", params={"email": "new@example.edu"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@example.edu for Test Club"
    }
    assert test_activities["Test Club"]["participants"] == [
        "existing@example.edu",
        "new@example.edu",
    ]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Missing/signup", params={"email": "new@example.edu"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Test%20Club/signup", params={"email": "existing@example.edu"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_rejects_full_activity(client):
    response = client.post(
        "/activities/Full%20Club/signup", params={"email": "new@example.edu"}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}


def test_unregister_removes_participant_and_frees_a_spot(client, test_activities):
    response = client.delete(
        "/activities/Crowded%20Club/signup", params={"email": "one@example.edu"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered one@example.edu from Crowded Club"
    }
    assert test_activities["Crowded Club"]["participants"] == ["two@example.edu"]

    signup_response = client.post(
        "/activities/Crowded%20Club/signup", params={"email": "one@example.edu"}
    )

    assert signup_response.status_code == 200
    assert test_activities["Crowded Club"]["participants"] == [
        "two@example.edu",
        "one@example.edu",
    ]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Missing/signup", params={"email": "one@example.edu"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_participant_not_signed_up(client, test_activities):
    response = client.delete(
        "/activities/Test%20Club/signup", params={"email": "missing@example.edu"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student not signed up for this activity"
    }
    assert test_activities["Test Club"]["participants"] == ["existing@example.edu"]
