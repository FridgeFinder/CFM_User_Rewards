"""DynamoDB helper functions for the User Rewards service."""

from typing import TypedDict, NotRequired
import logging
from typing import Any
from rules import ACTION_TYPES
from datetime import datetime, timezone
log = logging.getLogger(__name__)
import botocore.exceptions
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from models import UserPointsHistoryItem
from models import StatusReport
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
    new_report: StatusReport,
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
        item = UserPointsHistoryItem(
            userId=user_id,
            awardId=award_id,
            newReport=new_report,
            actionTypes=[action.name for action in awards],
            points=total,
            occurredAt=int(new_report["epochTimestamp"]),
            createdAt=datetime.now(timezone.utc)
                .strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        )
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


# ---------------------------------------------------------------------------
# UserActionStats
# ---------------------------------------------------------------------------
def update_user_action_stats(
    client, table_name: str, user_id: str, awards: list[ACTION_TYPES]
) -> None:
    """Atomically increment UserActionStats for a user."""

    total = 0
    update_counters = []
    for action in awards: 
        total += action.value["points"]
        action_count_name = action.value["action_count_name"]
        update_counters.append(f"{action_count_name} = if_not_exists({action_count_name}, :zero) + :inc")

    update_expression = ("SET totalPoints = if_not_exists(totalPoints, :zero) + :total, "
    +", ".join(update_counters))

    client.update_item(
            TableName = table_name, 
            Key ={"userId": {"S": user_id}}, 
            UpdateExpression=update_expression,
            ExpressionAttributeValues= {
                ':inc': {"N": "1"},
                ':zero': {"N": "0"}, 
                ':total': {"N": str(total)}
        },
    )

