"""Unit tests for functions/get_user_action_stats."""

import json

import boto3
from moto import mock_aws
from unittest.mock import patch

from functions.get_user_action_stats.stats_queries import get_user_action_stats

_TABLE = "test_stats"


def _create_stats_table(client):
    client.create_table(
        TableName=_TABLE,
        KeySchema=[{"AttributeName": "userId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "userId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


# ---------------------------------------------------------------------------
# stats_queries.get_user_action_stats
# ---------------------------------------------------------------------------
class TestGetUserActionStatsQuery:
    @mock_aws
    def test_returns_item_when_found(self):
        client = boto3.client("dynamodb", region_name="us-east-1")
        _create_stats_table(client)
        client.put_item(
            TableName=_TABLE,
            Item={
                "userId": {"S": "user9"},
                "totalPoints": {"N": "50"},
                "fridgeReportCount": {"N": "5"},
            },
        )

        result = get_user_action_stats(client, _TABLE, "user9")

        assert result is not None
        assert result["userId"] == "user9"
        assert result["totalPoints"] == 50
        assert result["fridgeReportCount"] == 5

    @mock_aws
    def test_returns_none_when_not_found(self):
        client = boto3.client("dynamodb", region_name="us-east-1")
        _create_stats_table(client)

        result = get_user_action_stats(client, _TABLE, "unknown_user")

        assert result is None


# ---------------------------------------------------------------------------
# app.handler
# ---------------------------------------------------------------------------
class TestGetUserActionStatsHandler:
    def test_returns_400_when_path_parameters_is_none(self):
        from functions.get_user_action_stats.app import handler

        result = handler({"pathParameters": None}, None)

        assert result["statusCode"] == 400
        assert "userId" in json.loads(result["body"])["error"]

    def test_returns_400_when_user_id_missing_from_path(self):
        from functions.get_user_action_stats.app import handler

        result = handler({"pathParameters": {}}, None)

        assert result["statusCode"] == 400

    @patch("functions.get_user_action_stats.app.get_user_action_stats", return_value=None)
    def test_returns_404_when_user_not_found(self, _mock):
        from functions.get_user_action_stats.app import handler

        result = handler({"pathParameters": {"userId": "user9"}}, None)

        assert result["statusCode"] == 404
        assert json.loads(result["body"])["error"] == "User stats not found"

    @patch(
        "functions.get_user_action_stats.app.get_user_action_stats",
        return_value={"userId": "user9", "totalPoints": 50, "fridgeReportCount": 5},
    )
    def test_returns_200_with_stats(self, _mock):
        from functions.get_user_action_stats.app import handler

        result = handler({"pathParameters": {"userId": "user9"}}, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["userId"] == "user9"
        assert body["totalPoints"] == 50
