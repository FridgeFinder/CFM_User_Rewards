"""Unit tests for app.py"""

from app import *


class TestProcessEvent:
    def test_processes_event(self):
        event = {
        "detail": {
            "userId": "user2",
            "newReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1762032699",
                "condition": "good",
                "foodPercentage": 2
            }),
            "previousReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1700000000",
                "condition": "dirty",
                "foodPercentage": 0
            }),
        }
    }

    result = _process_event(event "test-1")
    assert result == {"requestID": "test-1", "userId": "user2", "awards:"[{"points": 10}]}
        
    def test_processes_event_nullUser(self):
        event = {
        "detail": {
            "userId": "<null>",
            "newReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1762032699",
                "condition": "good",
                "foodPercentage": 2
            }),
            "previousReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1700000000",
                "condition": "dirty",
                "foodPercentage": 0
            }),
        }
    }

    result = _process_event(event "test-2")
    assert result == {"skipped": True}
        

