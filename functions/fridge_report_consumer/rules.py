"""Points rules for the User Rewards service."""

from __future__ import annotations
from enum import Enum
from models import AwardResult

"""
#NOTE: Do we want to keep track of when a user marks a fridge as "Dirty" or "Repaired"?
To reward people who make these specific status updates? 
"""


class ACTION_TYPES(Enum):
    FRIDGE_CLEANED = AwardResult(points=15, action_count_name="cleanedCount")
    FRIDGE_FILLED = AwardResult(points=10, action_count_name="filledCount")
    FRIDGE_REPAIRED = AwardResult(points=25, action_count_name="repairedCount")
    FRIDGE_REPORT = AwardResult(points=5, action_count_name="fridgeReportCount")


def get_fridge_report_awards(
    new_report: str, previous_report: str
) -> list[ACTION_TYPES]:
    """
    TODO: implement logic to compare new_report and previous_report and return a list of AwardResult
    NOTE: new_report and previous_report are json string, convert to dict. they can also be "<null>"
          see /events files for references on input
    #dirty -> cleaned: should be FRIDGE_CLEANED
    #food level > 0: should be FRIDGE_FILLED
    #needs repairs -> good: should be FRIDGE_REPAIRED
    #any report: should be FRIDGE_REPORT
    #combine condition and foodPercentage to get double points: cleaned + filled, repaired + filled
    """
    pass
