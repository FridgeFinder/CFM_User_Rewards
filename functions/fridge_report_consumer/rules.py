"""Points rules for the User Rewards service."""

from __future__ import annotations
from enum import Enum
from models import AwardResult, StatusReport
import json
from typing import TypedDict


"""
#NOTE: Do we want to keep track of when a user marks a fridge as "Dirty" or "Repaired"?
To reward people who make these specific status updates? 
"""

class ACTION_TYPES(Enum):
    FRIDGE_CLEANED = AwardResult(points=15, action_count_name="cleanedCount")
    FRIDGE_FILLED = AwardResult(points=10, action_count_name="filledCount")
    FRIDGE_REPAIRED = AwardResult(points=25, action_count_name="repairedCount")
    FRIDGE_REPORT = AwardResult(points=5, action_count_name="fridgeReportCount")

# Function takes in the new Report / old Report and returns a status report 
# with the fridgeId, timestamp, condiiton, and food percentage.
def parse_report(raw: str | None) -> StatusReport | None:
    if not raw or raw == "<null>":
        return None
    try:
        data = json.loads(raw)

        return StatusReport(
            fridgeId=data["fridgeId"],
            epochTimestamp=int(data["epochTimestamp"]),
            condition=data["condition"],
            foodPercentage=int(data["foodPercentage"]),
            userId=data.get("userId", None)
        )
    except KeyError as e:
        raise ValueError(f"Validation Error: Missing mandatory field {e}") from e

    except (ValueError, TypeError) as e:
        raise ValueError(f"Validation Error: Data type mismatch: {e}") from e




def get_fridge_report_awards(
    new_report: StatusReport, previous_report: StatusReport | None,
) -> list[ACTION_TYPES]:
    """
    TODO: implement logic to compare new_report and previous_report and return a list of AwardResult
    NOTE: new_report and previous_report are json string, convert to dict. they can also be "<null>"
          see /events files for references on input
    #dirty -> cleaned: should be FRIDGE_CLEANED
    #food level > 0: should be FRIDGE_FILLED 
    #out of order -> good: should be FRIDGE_REPAIRED
    #any report: should be FRIDGE_REPORT
    #combine condition and foodPercentage to get double points: cleaned + filled, repaired + filled
    """
    if previous_report is None:
        return [ACTION_TYPES.FRIDGE_REPORT]

    list_action_types = []
    new_cond = new_report["condition"]
    old_cond = previous_report["condition"]
    new_percentage = new_report["foodPercentage"]
    old_percentage = previous_report["foodPercentage"]

# 1. food level > 0: should be FRIDGE_FILLED 
    if int(new_percentage) > 0: 
        list_action_types.append(ACTION_TYPES.FRIDGE_FILLED)
# 2. dirty -> cleaned: should be FRIDGE_CLEANED
    if old_cond == "dirty" and new_cond == "good": 
        list_action_types.append(ACTION_TYPES.FRIDGE_CLEANED)
# 3. repairs -> good, should be FRIDGE_REPAIRED
    if old_cond == "out of order" and new_cond == "good":
        list_action_types.append(ACTION_TYPES.FRIDGE_REPAIRED)
# 4. any report: should be FRIDGE_REPORT
    list_action_types.append(ACTION_TYPES.FRIDGE_REPORT)
    return list_action_types

