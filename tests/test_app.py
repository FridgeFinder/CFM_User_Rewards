"""Unit tests for app.py"""

import json
import os
os.environ["USER_ACTION_STATS_TABLE"] = "test"
os.environ["USER_POINTS_HISTORY_TABLE"] = "test"
from functions.fridge_report_consumer.rules import *
from unittest.mock import patch
from functions.fridge_report_consumer.app import _process_event
# from dynamo import *
@patch("functions.fridge_report_consumer.app.write_user_points_history", return_value=True)
@patch("functions.fridge_report_consumer.app.update_user_action_stats")
@patch("functions.fridge_report_consumer.app.get_fridge_report_awards", return_value = [{"points": 15}])
class TestProcessEvent:
    # expected functionality is to return the dict with the request if user id and award of 15, since
    # the fridge was cleaned. Patch returns the award value of 15, but will be 
    # checked in yest_rules.py
    def test_processes_event(self, mock_awards, mock_update, mock_write):
        event = {
            "detail": {
            "userId": "user2",
            "newReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1762032699",
                "condition": "cleaned",
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
        result = _process_event(event, "test-1")
        assert result == {"requestId": "test-1", "userId": "user2", "awards":[{"points": 15}]}


       # expected functionality is to return skipped in a dict, since 
       # there must be a user defined or null 
    def test_processes_event_noUser(self, mock_awards, mock_update, mock_write):
        event = {
            "detail": {
            "userId": "",
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

        result = _process_event(event, "test-2")
        assert result == {"skipped": True}
        
        # expected functionality is to run as usual since should continue even if the 
        # user is null
def test_processes_event_nullUser(self, mock_awards, mock_update, mock_write):
        
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

        result = _process_event(event, "test-2")
        assert result == {"skipped": True}
        
