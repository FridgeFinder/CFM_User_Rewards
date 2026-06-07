"""Lambda handler — GET /user-action-stats/{userId}

Queries the UserActionStats DynamoDB table by userId and returns the item.
"""

from __future__ import annotations

import json
import os
from typing import Any

import logging

import boto3

from stats_queries import get_user_action_stats

log = logging.getLogger(__name__)


def get_ddb_client() -> boto3.client:
    """Return a DynamoDB client pointed at LocalStack or AWS."""
    deployment_target = os.getenv("DEPLOYMENT_TARGET", "local")
    if deployment_target == "aws":
        return boto3.client("dynamodb")
    return boto3.client("dynamodb", endpoint_url="http://localstack:4566")

dynamodb_client = get_ddb_client()
stats_table_name: str = os.environ["USER_ACTION_STATS_TABLE"]

def handler(event: dict[str, Any], context: Any) -> dict:
    """Return the UserActionStats record for a single user."""
    user_id = (event.get("pathParameters") or {}).get("userId")
    if not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "userId path parameter is required"}),
        }

    log.info("Querying UserActionStats for userId=%s", user_id)

    item = get_user_action_stats(dynamodb_client, stats_table_name, user_id)

    if item is None:
        log.info("No stats found for userId=%s", user_id)
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "User stats not found"}),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(item, default=str),
    }
