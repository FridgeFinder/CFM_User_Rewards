"""DynamoDB helpers for the Get User Action Stats function."""

from __future__ import annotations

import logging
from boto3.dynamodb.types import TypeDeserializer

log = logging.getLogger(__name__)

_deserializer = TypeDeserializer()


def _from_dynamo_item(item: dict) -> dict:
    return {k: _deserializer.deserialize(v) for k, v in item.items()}


def get_user_action_stats(client, table_name: str, user_id: str) -> dict | None:
    """Fetch a single UserActionStats record by userId.



    
    Returns the deserialised item, or None if not found.
    """
    response = client.get_item(
        TableName=table_name,
        Key={"userId": {"S": user_id}},
    )
    item = response.get("Item")
    if item is None:
        return None
    return _from_dynamo_item(item)
