
from __future__ import annotations

import logging
from boto3.dynamodb.types import TypeDeserializer

log = logging.getLogger(__name__)

_deserializer = TypeDeserializer()

def _from_dynamo_item(item: dict) -> dict:
    return {
        key: _deserializer.deserialize(value)
        for key, value in item.items()
    }

def return_fridge_report_notes(client, table_name: str,limit:int = 20, last_evaluated_key: dict| None = None) -> dict | None:
    """return fridge report notes in a dictionary for pagination.
    Returns the deserialised item, or None if not found.
    """
    request = {
        "TableName": table_name,
        "Limit": limit,
    }

    if last_evaluated_key: 
        request["ExclusiveStartKey"] = last_evaluated_key

    response = client.scan(**request)
    # getting the items in the userpointshistory table
    results = []
    for item in response.get("Items", []):
        deserializedItem = _from_dynamo_item(item)
        results.append({
            "newReport": deserializedItem.get("newReport", {}),
            "points": deserializedItem.get("points"),
            "actionTypes": deserializedItem.get("actionTypes", []),
            "awardId": deserializedItem.get("awardId")
    })
    return {
        "items": results, 
        "lastEvaluatedKey": response.get("LastEvaluatedKey")
    }