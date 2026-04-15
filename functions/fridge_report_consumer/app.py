"""Lambda handler for the User Rewards Consumer."""

from __future__ import annotations
from typing import Any, List
from logging_utils import configure_logging, get_logger
from rules import ACTION_TYPES, get_fridge_report_awards, parse_report
from dynamo import write_user_points_history, update_user_action_stats
import os
import boto3
import json


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
    ### GET DATA FROM EVENT ###
    detail: dict = event.get("detail") or {}
    new_report_raw = detail.get("newReport", "<null>")
    previous_report_raw = detail.get("previousReport", "<null>")
    ### PARSE DATA ###
    try: 
        new_report = parse_report(new_report_raw)
        previous_report = parse_report(previous_report_raw)
    except ValueError as e: 
        log.error("Not valid report data")
        return {
            "skipped": True, 
            "requestId": request_id, 
            "reason": "invalid_data"}
    ### PROCESS/VALIDATE DATA ###
    if new_report is None:
        return {"skipped": True, "requestId": request_id, "message": "new report is null"}
    if not new_report.get("userId"):
        return {"skipped": True, "requestId": request_id, "message": "user id is null"}
    if (new_report == previous_report):
        return {"skipped": True, "requestId": request_id, "message": "new and old report are the same"}
    user_id = new_report.get("userId")
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
    ### BUSINESS/DATA LOGIC ###
    award_id = f"AWARD#STATUS_UPDATE#FRIDGE#{new_report['fridgeId']}#TS#{new_report['epochTimestamp']}"
    awards: List[ACTION_TYPES] = get_fridge_report_awards(new_report, previous_report)
    if write_user_points_history(dynamodb_client, user_points_history_table_name, user_id, award_id, new_report, awards):
        update_user_action_stats(dynamodb_client, user_action_stats_table_name, user_id, awards)
        return {"requestId": request_id, "userId": user_id, "awards": [a.value for a in awards]}
    else:
        return {"skipped": True, "requestId": request_id, "message": "duplicate"}