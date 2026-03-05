"""DynamoDB helper functions for the User Rewards service."""

from __future__ import annotations

import logging
from typing import Any

from functions.fridge_report_consumer.rules import ACTION_TYPES

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# UserPointsHistory
# ---------------------------------------------------------------------------
def write_user_points_history(
    client,
    table_name: str,
    user_id: str,
    award_id: str,
    user_action: dict,
    awards: list[ACTION_TYPES],
) -> dict:
    # awardId generated awardId, example: STATUS_UPDATE#FRIDGE#{fridgeId}#TS#{epochTimestamp}
    # NOTE: user_action: we can save this as a string or a map. I think map?
    # NOTE: user_action is new_report
    """Conditionally write a points record.

    Uses a ConditionExpression to prevent duplicate awards for the same
    (userId, awardId) pair.

    Returns:
        True  — item was written successfully (first time).
        False — item already existed (duplicate);

    Raises:
        ClientError for errors other than ConditionalCheckFailedException.
    """
    pass


# ---------------------------------------------------------------------------
# UserActionStats
# ---------------------------------------------------------------------------
def update_user_action_stats(
    client, table_name: str, user_id: str, awards: list[ACTION_TYPES]
) -> dict:
    """Atomically increment UserActionStats for a user.
    #TODO: implement
    #NOTE: for reference: https://oneuptime.com/blog/post/2026-02-12-dynamodb-atomic-counters/view
    #NOTE: use whichever expression makes sense for your use case
    Returns:
        The full, updated stats item
    """
    return _dynamo_item_to_dict()


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
