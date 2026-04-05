"""DynamoDB helper functions for the User Rewards service."""

from __future__ import annotations

import logging
from typing import Any
from functions.fridge_report_consumer.rules import ACTION_TYPES
from datetime import datetime, timezone
log = logging.getLogger(__name__)
import botocore.exceptions
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from functions.fridge_report_consumer.models import UserPointsHistoryItem

# ---------------------------------------------------------------------------
# UserPointsHistory
# ---------------------------------------------------------------------------

_serializer = TypeSerializer()
_deserializer = TypeDeserializer()


def _to_dynamo_item(item: dict) -> dict:
    """Serialise a plain Python dict to a DynamoDB typed item."""
    return {k: _serializer.serialize(v) for k, v in item.items()}


def _from_dynamo_item(item: dict) -> dict:
    """Deserialise a raw DynamoDB typed item to a plain Python dict."""
    return {k: _deserializer.deserialize(v) for k, v in item.items()}

# write to the database, return true if item written successfully, false if not
#  writing to the dynamo db database
def write_user_points_history(
    client,
    table_name: str,
    user_id: str,
    award_id: str,
    new_report: dict, 
    awards: list[ACTION_TYPES], 
) -> dict:
    # awardId generated awardId, example: STATUS_UPDATE#FRIDGE#{fridgeId}#TS#{epochTimestamp}

    """Conditionally write a points record.

    Uses a ConditionExpression to prevent duplicate awards for the same
    (userId, awardId) pair.

    Returns:
        True  — item was written successfully (first time).
        False — item already existed (duplicate);

    Raises:
        ClientError for errors other than ConditionalCheckFailedException.
    """
    # if 2 different ACTION TYPES Logged for the user in the singular
    # log of the event, then we want to sum the total points.

    # compute the total points, if the user had more than one action type, 
    # sum to get the total points that should be added for the singular event
    total = 0
    # compute points totaled
    for action in awards: 
        total += action.value["points"]
    try:
        item: UserPointsHistoryItem = {
            "userId": user_id,
            "awardId": award_id,
            "newReport": new_report,
            "action_types": [action.name for action in awards],
            "points": total,
            "occurredAt": int(new_report["epochTimestamp"]),
            "createdAt": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',  # cleaner than int→str
        }
        # use a condition check to make sure both the user_id and award_id are unique pair
        conditionalUpdateResponse = client.put_item(
            TableName = table_name, 
            Item =_to_dynamo_item(item), 
            ConditionExpression= 'attribute_not_exists(userId) AND attribute_not_exists(awardId)'
        )
        return True
    except botocore.exceptions.ClientError as x:
        # if the error was a conditional exception, specify, otherwise they are all considered
        # to be client errors
        errorCode = x.response.get("Error", {}).get("Code")
        if errorCode == "ConditionalCheckFailedException":
            log.exception("A Conditional Check Failed Exception Occurred")
            return False
        # handle condition failed
        else:
            log.exception("A client error occurred")
            raise
            return False  # handle other ClientErrors


# ---------------------------------------------------------------------------
# UserActionStats
# ---------------------------------------------------------------------------
def update_user_action_stats(
    client, table_name: str, user_id: str, awards: list[ACTION_TYPES]
) -> dict:
    """Atomically increment UserActionStats for a user.
   
    Returns:
        The full, updated stats item
    """

    total = 0
    update_counters = []
    for action in awards: 
        total += action.value["points"]
        action_count_name = action.value["action_count_name"]
        update_counters.append(f"{action_count_name} = if_not_exists({action_count_name}, :zero) + :inc")

    update_expression = ("SET totalPoints = if_not_exists(totalPoints, :zero) + :total, "
    +", ".join(update_counters))

    response = client.update_item(
            TableName = table_name, 
            Key ={"user_id": {"S": user_id}}, 
            UpdateExpression=update_expression,
            ExpressionAttributeValues= {
                ':inc': {"N": "1"},
                ':zero': {"N": "0"}, 
                ':total': {"N": str(total)}
        }
    )
    
    return _from_dynamo_item(response["Attributes"])


# ---------------------------------------------------------------------------
# Internal serialisation helpers
# ---------------------------------------------------------------------------


def _dict_to_dynamo_map(d: dict) -> dict:
    """Shallow conversion of a plain dict to a DynamoDB Map type descriptor."""
    return {"M": {k: _python_to_dynamo(v) for k, v in d.items()}}


# NOTE: didn't test not sure if this works
def _python_to_dynamo(value: Any) -> dict:
    """Best-effort conversion of a Python scalar/collection to DynamoDB type."""
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, int):
        return {"N": str(value)}
    if isinstance(value, str):
        return {"S": value}
    if isinstance(value, dict):
        return _dict_to_dynamo_map(value)
    if isinstance(value, list):
        return {"L": [_python_to_dynamo(v) for v in value]}
    if value is None:
        return {"NULL": True}
    # Fallback: stringify
    return {"S": str(value)}


# Note: didn't test not sure if this works
def _dynamo_item_to_dict(item: dict) -> dict:
    """Deserialise a raw DynamoDB item dict to plain Python types."""
    return {k: _dynamo_to_python(v) for k, v in item.items()}


# NOTE: didn't test not sure if this works
def _dynamo_to_python(descriptor: dict) -> Any:
    """Convert a single DynamoDB attribute descriptor to a Python value."""
    if "S" in descriptor:
        return descriptor["S"]
    if "N" in descriptor:
        raw = descriptor["N"]
        return int(raw)
    if "BOOL" in descriptor:
        return descriptor["BOOL"]
    if "NULL" in descriptor:
        return None
    if "M" in descriptor:
        return _dynamo_item_to_dict(descriptor["M"])
    if "L" in descriptor:
        return [_dynamo_to_python(v) for v in descriptor["L"]]
    return descriptor  # Unknown — return raw
