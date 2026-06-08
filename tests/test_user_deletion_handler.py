"""Unit tests for functions/user_deletion_handler."""

import boto3
from moto import mock_aws
from unittest.mock import patch

import functions.user_deletion_handler.app as deletion_app

_HISTORY_TABLE = "test_history"
_STATS_TABLE = "test_stats"


def _create_tables(client):
    client.create_table(
        TableName=_HISTORY_TABLE,
        KeySchema=[
            {"AttributeName": "userId", "KeyType": "HASH"},
            {"AttributeName": "awardId", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "awardId", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    client.create_table(
        TableName=_STATS_TABLE,
        KeySchema=[{"AttributeName": "userId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "userId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


# ---------------------------------------------------------------------------
# app.handler — input validation
# ---------------------------------------------------------------------------
class TestUserDeletionHandlerValidation:
    def test_skips_when_detail_is_empty(self):
        result = deletion_app.handler({"detail": {}}, None)
        assert result == {"skipped": True, "reason": "missing_userId"}

    def test_skips_when_detail_key_missing(self):
        result = deletion_app.handler({}, None)
        assert result == {"skipped": True, "reason": "missing_userId"}


# ---------------------------------------------------------------------------
# app.handler — deletion logic
# ---------------------------------------------------------------------------
class TestUserDeletionHandlerDeletion:
    @mock_aws
    def test_deletes_history_and_stats_for_user(self):
        client = boto3.client("dynamodb", region_name="us-east-1")
        _create_tables(client)
        client.put_item(
            TableName=_HISTORY_TABLE,
            Item={"userId": {"S": "user9"}, "awardId": {"S": "award1"}},
        )
        client.put_item(
            TableName=_STATS_TABLE,
            Item={"userId": {"S": "user9"}, "totalPoints": {"N": "50"}},
        )

        with patch.object(deletion_app, "dynamodb_client", client), \
             patch.object(deletion_app, "points_history_table_name", _HISTORY_TABLE), \
             patch.object(deletion_app, "action_stats_table_name", _STATS_TABLE):
            result = deletion_app.handler({"detail": {"userId": "user9"}}, None)

        assert result == {"deleted": True, "userId": "user9"}
        assert "Item" not in client.get_item(
            TableName=_HISTORY_TABLE,
            Key={"userId": {"S": "user9"}, "awardId": {"S": "award1"}},
        )
        assert "Item" not in client.get_item(
            TableName=_STATS_TABLE,
            Key={"userId": {"S": "user9"}},
        )

    @mock_aws
    def test_does_not_delete_other_users_data(self):
        client = boto3.client("dynamodb", region_name="us-east-1")
        _create_tables(client)
        client.put_item(
            TableName=_HISTORY_TABLE,
            Item={"userId": {"S": "user9"}, "awardId": {"S": "award1"}},
        )
        client.put_item(
            TableName=_HISTORY_TABLE,
            Item={"userId": {"S": "other_user"}, "awardId": {"S": "award1"}},
        )

        with patch.object(deletion_app, "dynamodb_client", client), \
             patch.object(deletion_app, "points_history_table_name", _HISTORY_TABLE), \
             patch.object(deletion_app, "action_stats_table_name", _STATS_TABLE):
            deletion_app.handler({"detail": {"userId": "user9"}}, None)

        other = client.get_item(
            TableName=_HISTORY_TABLE,
            Key={"userId": {"S": "other_user"}, "awardId": {"S": "award1"}},
        )
        assert "Item" in other

    @mock_aws
    def test_batch_deletes_more_than_25_history_records(self):
        client = boto3.client("dynamodb", region_name="us-east-1")
        _create_tables(client)
        for i in range(30):
            client.put_item(
                TableName=_HISTORY_TABLE,
                Item={"userId": {"S": "user9"}, "awardId": {"S": f"award{i}"}},
            )

        with patch.object(deletion_app, "dynamodb_client", client), \
             patch.object(deletion_app, "points_history_table_name", _HISTORY_TABLE), \
             patch.object(deletion_app, "action_stats_table_name", _STATS_TABLE):
            deletion_app._delete_points_history("user9")

        remaining = client.query(
            TableName=_HISTORY_TABLE,
            KeyConditionExpression="userId = :uid",
            ExpressionAttributeValues={":uid": {"S": "user9"}},
        )
        assert remaining["Count"] == 0
