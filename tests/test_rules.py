"""Unit tests for rules.py"""
from enum import Enum
import json
from functions.fridge_report_consumer.rules import ACTION_TYPES
from functions.fridge_report_consumer.models import AwardResult
from functions.fridge_report_consumer.rules import get_fridge_report_awards


class TestGetFridgeReportAwards:
    #NOTE: remove this test once the function is implemented
    def test_returns_cleaned(self):
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

        result = get_fridge_report_awards(event["detail"]["newReport"], event["detail"]["previousReport"])
        assert ACTION_TYPES.FRIDGE_FILLED in result
        assert ACTION_TYPES.FRIDGE_CLEANED in result
        assert ACTION_TYPES.FRIDGE_REPORT in result
        assert len(result) == 3        



    def test_returns_repairs(self):
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
                "condition": "needs repairs",
                "foodPercentage": 0
            }),
        }
        }

        result = get_fridge_report_awards(event["detail"]["newReport"], event["detail"]["previousReport"])
        assert ACTION_TYPES.FRIDGE_FILLED in result
        assert ACTION_TYPES.FRIDGE_REPAIRED in result
        assert ACTION_TYPES.FRIDGE_REPORT in result
        assert len(result) == 3        
