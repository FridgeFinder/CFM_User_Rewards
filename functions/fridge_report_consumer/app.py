"""Lambda handler for the User Rewards Consumer."""

from __future__ import annotations
from typing import Any, List
from .logging_utils import configure_logging, get_logger
from .rules import ACTION_TYPES, get_fridge_report_awards
from .dynamo import *
import os
import boto3
import json
import uuid


def get_ddb_client() -> boto3.client:
    """
    Get DynamoDB client with support for local testing
    Set DEPLOYMENT_TARGET=local to connect to LocalStack
    """
    deployment_target = os.getenv("DEPLOYMENT_TARGET", "local")
    if deployment_target == "aws":
        return boto3.client("dynamodb")
    else:
        return boto3.client("dynamodb", endpoint_url="http://localstack:4566")


# Cold-start initialisation
configure_logging()
log = get_logger(__name__)
dynamodb_client = get_ddb_client()
user_action_stats_table_name: str = os.environ["USER_ACTION_STATS_TABLE"]
user_points_history_table_name: str = os.environ["USER_POINTS_HISTORY_TABLE"]


def handler(event: dict[str, Any], context: Any) -> dict:
    """Lambda entry point — single EventBridge event delivery."""
    request_id: str = getattr(context, "aws_request_id", "local")
    return _process_event(event, request_id)


def _process_event(event: dict[str, Any], request_id: str) -> dict:
    detail: dict = event.get("detail") or {}

    # if user_id is missing, skip processing
    # NOTE: userId can be "<null>" if the report is made by a user that's not logged in
    # NOTE: should we keep track of anonymous user activity? I think so..
    # NOTE: it's possible newReport and previousReport are the same, if that occurs you can skip processing
    user_id = detail.get("userId", "<null>")
    new_report = detail.get("newReport", "<null>")
    previous_report = detail.get("previousReport", "<null>")
    if user_id == "<null>":
        return {"skipped": True, "requestId": request_id, "message": "user id is null"}

# 1. convert the string to json
    # json_user_id = json.loads(user_id)
    json_new_report = json.loads(new_report)
    json_previous_report = json.loads(previous_report)

    if (json_new_report == json_previous_report):
        return {"skipped": True, "requestId": request_id, "message": "new and old report are the same"}
    
# 2. generate the award id using AWARD#STATUS_UPDATE#FRIDGE#{fridgeId}#TS#{timestamp}
    award_id = f"AWARD#STATUS_UPDATE#FRIDGE#{json_new_report['fridgeId']}#TS#{json_new_report['epochTimestamp']}"
    # get the list of ACTION TYPES using the  (rules.py) function, get fridge report awards
    awards: List[ACTION_TYPES] = get_fridge_report_awards(new_report, previous_report)

# 3. Write to the user_points_history table. if the history write succeeds, then update the user_action_stats table
    # write to user points history table ( dynamo.py ), if successful, then update the user_action_stats table
    if write_user_points_history(dynamodb_client, user_points_history_table_name, user_id, award_id, json_new_report, awards):
        update_user_action_stats(dynamodb_client, user_action_stats_table_name, user_id, awards)

# maybe convert the null to none, if its null we want to skip procedure because we dont want to report

    log.info(
        "FridgeReportUpdated received",
        extra={
            "requestId": request_id,
            "userId": user_id,
            "newReport": new_report,
            "previousReport": previous_report,
            "user_points_history_table": user_points_history_table_name,
            "user_action_stats_table": user_action_stats_table_name,
        },
    )
    return {"requestId": request_id, "userId": user_id, "awards": awards}
