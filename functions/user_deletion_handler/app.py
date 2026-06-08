"""Lambda handler — User Deletion Cleanup

Triggered by a 'User Deleted' EventBridge event from the user-service.
Removes all reward data for the deleted user:
  - All rows in UserPointsHistory (Query by userId, then batch delete)
  - The single row in UserActionStats (DeleteItem by userId)
"""

from __future__ import annotations

import os
from typing import Any

import boto3
import botocore.exceptions

from logging_utils import configure_logging, get_logger


def get_ddb_client() -> boto3.client:
    """Return a DynamoDB client pointed at LocalStack or AWS."""
    deployment_target = os.getenv("DEPLOYMENT_TARGET", "local")
    if deployment_target == "aws":
        return boto3.client("dynamodb")
    return boto3.client("dynamodb", endpoint_url="http://localstack:4566")


# Cold-start initialisation
configure_logging()
log = get_logger(__name__)
dynamodb_client = get_ddb_client()
points_history_table_name: str = os.environ["USER_POINTS_HISTORY_TABLE"]
action_stats_table_name: str = os.environ["USER_ACTION_STATS_TABLE"]


def handler(event: dict[str, Any], context: Any) -> dict:
    """Delete all reward records for a user that has been removed."""
    detail: dict = event.get("detail") or {}
    user_id: str | None = detail.get("userId")

    if not user_id:
        log.error("User Deleted event missing userId", extra={"event": event})
        return {"skipped": True, "reason": "missing_userId"}

    log.info("Deleting reward data for user", extra={"userId": user_id})

    _delete_points_history(user_id)
    _delete_action_stats(user_id)

    log.info("Reward data deleted for user", extra={"userId": user_id})
    return {"deleted": True, "userId": user_id}


def _delete_points_history(user_id: str) -> None:
    """Query all UserPointsHistory records for a user and batch-delete them."""
    last_evaluated_key = None
    total_deleted = 0

    while True:
        query_kwargs: dict = {
            "TableName": points_history_table_name,
            "KeyConditionExpression": "userId = :uid",
            "ExpressionAttributeValues": {":uid": {"S": user_id}},
            "ProjectionExpression": "userId, awardId",
        }
        if last_evaluated_key:
            query_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = dynamodb_client.query(**query_kwargs)
        items = response.get("Items", [])

        # batch_write_item accepts at most 25 requests per call
        for i in range(0, len(items), 25):
            batch = items[i : i + 25]
            dynamodb_client.batch_write_item(
                RequestItems={
                    points_history_table_name: [
                        {
                            "DeleteRequest": {
                                "Key": {
                                    "userId": item["userId"],
                                    "awardId": item["awardId"],
                                }
                            }
                        }
                        for item in batch
                    ]
                }
            )
            total_deleted += len(batch)

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    log.info(
        "Deleted UserPointsHistory records for user",
        extra={"userId": user_id, "count": total_deleted},
    )


def _delete_action_stats(user_id: str) -> None:
    """Delete the UserActionStats record for a user."""
    try:
        dynamodb_client.delete_item(
            TableName=action_stats_table_name,
            Key={"userId": {"S": user_id}},
        )
        log.info(
            "Deleted UserActionStats record for user", extra={"userId": user_id}
        )
    except botocore.exceptions.ClientError:
        log.exception(
            "Failed to delete UserActionStats record", extra={"userId": user_id}
        )
        raise
