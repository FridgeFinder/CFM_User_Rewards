"""Lambda handler for the User Rewards Consumer."""

from __future__ import annotations
from typing import Any, List
from logging_utils import configure_logging, get_logger
from rules import ACTION_TYPES, get_fridge_report_awards
import os
import boto3


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
    # TODO: create user "Anonymous_Neighbor" and use that userId in the statusReport
    # NOTE: Don't have to do anything here.. FridgeReport can handle that but keeping note here in case we forget
    # NOTE: it's possible newReport and previousReport are the same, if that occurs you can skip processing
    user_id = detail.get("userId", "<null>")
    new_report = detail.get("newReport", "<null>")
    previous_report = detail.get("previousReport", "<null>")

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

    awards: List[ACTION_TYPES] = get_fridge_report_awards(new_report, previous_report)
    # TODO: write to user_points_history table. If history write succeeds, update user_action_stats table

    return {"requestId": request_id, "userId": user_id, "awards": awards}
