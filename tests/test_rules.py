"""Unit tests for rules.py"""
from enum import Enum
import json
from functions.fridge_report_consumer.rules import ACTION_TYPES
from functions.fridge_report_consumer.models import AwardResult, StatusReport
from functions.fridge_report_consumer.rules import get_fridge_report_awards, parse_report


class TestGetFridgeReportAwards:
    def test_returns_only_fridgereport(self): 
        

        newReport: StatusReport = {
            "fridgeId": "greenpointfridge", 
            "epochTimestamp": 1762032699, 
            "condition": "good", 
            "foodPercentage": 75,
            "note":"deep cleaned the fridge and aided stocking efforts"

        }

        result = get_fridge_report_awards(newReport, None)
        assert ACTION_TYPES.FRIDGE_REPORT in result




    def test_returns_cleaned(self):

        prevReport: StatusReport = {
            "fridgeId": "greenpointfridge",
            "epochTimestamp": 1762032699,
            "condition": "dirty",
            "foodPercentage": 70,
            "note":"deep cleaned the fridge and aided stocking efforts"

        }

        newReport: StatusReport = {
            "fridgeId": "greenpointfridge", 
            "epochTimestamp": 1762032699, 
            "condition": "good", 
            "foodPercentage": 75,
            "note":"deep cleaned the fridge and aided stocking efforts"

        }



        result = get_fridge_report_awards(newReport, prevReport)
        assert ACTION_TYPES.FRIDGE_FILLED in result
        assert ACTION_TYPES.FRIDGE_CLEANED in result
        assert ACTION_TYPES.FRIDGE_REPORT in result
        assert len(result) == 3        



    def test_returns_repairs(self):
        prevReport: StatusReport = {
            "fridgeId": "greenpointfridge",
            "epochTimestamp": 1762032699,
            "condition": "out of order",
            "foodPercentage": 70,
            "note":"deep cleaned the fridge and aided stocking efforts"

        }

        newReport: StatusReport = {
            "fridgeId": "greenpointfridge", 
            "epochTimestamp": 1762032699, 
            "condition": "good", 
            "foodPercentage": 75,
            "note":"deep cleaned the fridge and aided stocking efforts"

        }


        result = get_fridge_report_awards(newReport, prevReport)
        assert ACTION_TYPES.FRIDGE_FILLED in result
        assert ACTION_TYPES.FRIDGE_REPAIRED in result
        assert ACTION_TYPES.FRIDGE_REPORT in result
        assert len(result) == 3     

    def test_parse_report(self):
        VALID_NEW_REPORT = json.dumps({
            "fridgeId": "greenpointfridge",
            "epochTimestamp": "1762032699",
            "condition": "good",
            "foodPercentage": 50,
            "userId": "user1",
        })

        VALID_PREVIOUS_REPORT = json.dumps({
            "fridgeId": "greenpointfridge",
            "epochTimestamp": "1800000000",
            "condition": "dirty",
            "foodPercentage": 0,
            "userId": "user1",
        })
        reportExpectedNew: StatusReport = {
            "fridgeId": "greenpointfridge",
            "epochTimestamp": 1762032699,
            "condition": "good",
            "foodPercentage": 50,
            "userId": "user1",
            "note":"deep cleaned the fridge and aided stocking efforts"

        }

        reportExpectedPrev: StatusReport = {
            "fridgeId": "greenpointfridge",
            "epochTimestamp": "1800000000",
            "condition": "dirty",
            "foodPercentage": 0,
            "userId": "user1",
            "note":"deep cleaned the fridge and aided stocking efforts"

        }
        result1 = parse_report(VALID_NEW_REPORT)
        result2 = parse_report(VALID_PREVIOUS_REPORT)

        assert reportExpectedNew == result1
