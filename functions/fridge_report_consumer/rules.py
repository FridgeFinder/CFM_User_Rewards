"""Points rules for the User Rewards service."""

from __future__ import annotations
from enum import Enum
from models import AwardResult
import json

"""
#NOTE: Do we want to keep track of when a user marks a fridge as "Dirty" or "Repaired"?
To reward people who make these specific status updates? 
"""


class ACTION_TYPES(Enum):
    FRIDGE_CLEANED = AwardResult(points=15, action_count_name="cleanedCount")
    FRIDGE_FILLED = AwardResult(points=10, action_count_name="filledCount")
    FRIDGE_REPAIRED = AwardResult(points=25, action_count_name="repairedCount")
    FRIDGE_REPORT = AwardResult(points=5, action_count_name="fridgeReportCount")


# where the comparing is happening based on the 4 action types
# return a list of actin types, if a user has done 2 actions, return a list of action types, 
# based on the condition and the food percentage
# if good and filled and before it was dirty, it would return 2 things, since two actions
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
    list_action_types = []
    # 1. convert the previous and new report to a dict to access the condition + foodPercentage fields
    # in the case that the previous report is null
    if (previous_report == "<null"):
        json_previous_report = {}
    else:
        json_previous_report = json.loads(previous_report)

    json_new_report = json.loads(new_report)

    new_cond = json_new_report["condition"]
    old_cond = json_previous_report["condition"]

    new_percentage = json_new_report["foodPercentage"]
    old_percentage = json_previous_report["foodPercentage"]
# create list of action types based on conditions and percentage of food old vs. new
     #dirty -> cleaned: should be FRIDGE_CLEANED
    #needs repairs -> good: should be FRIDGE_REPAIRED
    #any report: should be FRIDGE_REPORT

 # 1. food level > 0: should be FRIDGE_FILLED 
    if int(new_percentage) > 0: 
        list_action_types.append(ACTION_TYPES.FRIDGE_FILLED)
# 2. dirty -> cleaned: should be FRIDGE_CLEANED
    if old_cond == "dirty" and new_cond == "cleaned": 
        list_action_types.append(ACTION_TYPES.FRIDGE_CLEANED)
# 3. repairs -> good, should be FRIDGE_REPAIRED
    if old_cond == "needs repairs" and new_cond == "good":
        list_action_types.append(ACTION_TYPES.FRIDGE_REPAIRED)
# 4. any report: should be FRIDGE_REPORT
    list_action_types.append(ACTION_TYPES.FRIDGE_REPORT)
    return list_action_types






    


