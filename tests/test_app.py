"""Unit tests for app.py"""

import json
import os
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
            "newReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1762032699",
                "condition": "cleaned",
                "foodPercentage": 2,
                "userId": "user2"
            }),
            "previousReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1700000000",
                "condition": "dirty",
                "foodPercentage": 0,
                "userId": "user2"
            
            }),
        }
    }
        result = _process_event(event, "test-1")
        assert result == {"requestId": "test-1", "userId": "user2", "awards":[{"points": 15}]}


       # expected functionality is to return skipped in a dict, since 
       # there must be a user defined or null 
    # def test_processes_event_noUser(self, mock_awards, mock_update, mock_write):
    #     event = {
    #         "detail": {
    #         "newReport": json.dumps({
    #             "fridgeId": "greenpointfridge",
    #             "epochTimestamp": "1762032699",
    #             "condition": "good",
    #             "foodPercentage": 2, 
    #             "userId": ""
                
    #         }),
    #         "previousReport": json.dumps({
    #             "fridgeId": "greenpointfridge",
    #             "epochTimestamp": "1700000000",
    #             "condition": "dirty",
    #             "foodPercentage": 0,
    #             "userId": ""

    #         }),
    #     }
    # }

    #     result = _process_event(event, "test-2")
    #     assert result == {"skipped": True, "requestId": "test-2", "message": "user id is null"}
        
        # expected functionality is to run as usual since should continue even if the 
        # user is null
    def test_processes_event_null_user(self, mock_awards, mock_update, mock_write):
        
        event = {
            "detail": {
            "newReport": json.dumps({
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1762032699",
                "condition": "good",
                "foodPercentage": 2, 
                "userId": "",

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
        assert result == {"skipped": True, "requestId": "test-2", "message": "user id is null"}
# ---------------------------------------------------------------------------
# Edge cases: null / missing newReport and previousReport
# ---------------------------------------------------------------------------
VALID_NEW_REPORT = json.dumps({
    "fridgeId": "greenpointfridge",
    "epochTimestamp": "1762032699",
    "condition": "good",
    "foodPercentage": 50,
    "userId": "user1",
})

VALID_PREVIOUS_REPORT = json.dumps({
    "fridgeId": "greenpointfridge",
    "epochTimestamp": "1700000000",
    "condition": "dirty",
    "foodPercentage": 0,
    "userId": "user1",
})


@patch("functions.fridge_report_consumer.app.write_user_points_history", return_value=True)
@patch("functions.fridge_report_consumer.app.update_user_action_stats")
class TestSkippedReportCases:
    def test_null_new_report_is_skipped(self, mock_update, mock_write):
        """newReport='<null>' means no report — should skip"""
        event = {"detail": {"newReport": "<null>", "previousReport": "<null>"}}
        result = _process_event(event, "test-null-new")
        assert result["skipped"] is True

    def test_null_previous_report_is_handled(self, mock_update, mock_write):
        """previousReport='<null>' is valid — first report for a fridge."""
        event = {"detail": {"newReport": VALID_NEW_REPORT, "previousReport": "<null>"}}
        result = _process_event(event, "test-null-prev")
        # assert result.get("skipped") is not True
        assert "skipped" not in result

    def test_new_report_identical_to_previous_is_skipped(self, mock_update, mock_write):
        """When newReport and previousReport are the same, event should be skipped."""
        event = {"detail": {"newReport": VALID_NEW_REPORT, "previousReport": VALID_NEW_REPORT}}
        result = _process_event(event, "test-same-report")
        assert result["skipped"] is True
        assert result["message"] == "new and old report are the same"


@patch("functions.fridge_report_consumer.app.write_user_points_history", return_value=False)
@patch("functions.fridge_report_consumer.app.update_user_action_stats")
class TestDuplicateWrite:
    """Tests for when DynamoDB signals a duplicate (condition check failed)."""

    def test_duplicate_write_skips_update(self, mock_update, mock_write):
        """When write returns False, update must NOT be called and response must be skipped."""
        event = {"detail": {"newReport": VALID_NEW_REPORT, "previousReport": VALID_PREVIOUS_REPORT}}
        result = _process_event(event, "test-dup")

        mock_write.assert_called_once()
        mock_update.assert_not_called()
        assert result["skipped"] is True
        assert result["message"] == "duplicate"

    def test_successful_write_calls_update(self, mock_update, mock_write):
        """When write returns True, update_user_action_stats must be called."""
        mock_write.return_value = True
        event = {"detail": {"newReport": VALID_NEW_REPORT, "previousReport": VALID_PREVIOUS_REPORT}}
        _process_event(event, "test-success")

        mock_write.assert_called_once()
        mock_update.assert_called_once()