import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.activity = {
            "description": "Test",
            "schedule": "Friday",
            "max_participants": 2,
            "participants": ["one+test@example.edu", "two@example.edu"],
        }
        self.activity_patch = patch.dict(activities, {"Test Club": self.activity})
        self.activity_patch.start()
        self.addCleanup(self.activity_patch.stop)
        self.addCleanup(self.client.close)

    def test_unregister_updates_activity_and_frees_a_spot(self):
        response = self.client.delete(
            "/activities/Test%20Club/signup", params={"email": "one+test@example.edu"}
        )
        self.assertEqual(response.status_code, 200)
        activity = self.client.get("/activities").json()["Test Club"]
        self.assertEqual(activity["participants"], ["two@example.edu"])
        self.assertEqual(activity["max_participants"] - len(activity["participants"]), 1)
        self.assertEqual(
            self.client.post(
                "/activities/Test%20Club/signup", params={"email": "one+test@example.edu"}
            ).status_code,
            200,
        )

    def test_missing_activity_or_participant_does_not_change_signups(self):
        missing_activity = self.client.delete(
            "/activities/Missing/signup", params={"email": "one+test@example.edu"}
        )
        self.assertEqual(missing_activity.status_code, 404)
        missing_participant = self.client.delete(
            "/activities/Test%20Club/signup", params={"email": "missing@example.edu"}
        )
        self.assertEqual(missing_participant.status_code, 404)
        self.assertEqual(
            self.activity["participants"], ["one+test@example.edu", "two@example.edu"]
        )


if __name__ == "__main__":
    unittest.main()
