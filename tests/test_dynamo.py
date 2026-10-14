
import boto3
from moto import mock_aws
import json 
from functions.fridge_report_consumer.dynamo import write_user_points_history
from functions.fridge_report_consumer.dynamo import update_user_action_stats
from functions.fridge_report_consumer.rules import ACTION_TYPES



class TestGetFridgeReportAwards:

    @mock_aws
    def test_write_user_points_history(self):
        client = boto3.client('dynamodb')
        awardListMock = [ACTION_TYPES.FRIDGE_CLEANED]
        client.create_table(
            TableName = "test_table", 
            KeySchema = [{"AttributeName": "userId", "KeyType": "HASH"}, 
            {"AttributeName": "awardId", "KeyType": "RANGE"}], 
            AttributeDefinitions = [
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "awardId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST"

            )

        newReportMock: StatusReport = {
            "fridgeId": "greenpointfridge", 
            "epochTimestamp": 1762032699, 
            "condition": "cleaned", 
            "foodPercentage": 2,
            "note":"deep cleaned the fridge and aided stocking efforts"

        }
        result = write_user_points_history(client, "test_table", "user1", "award1", newReportMock, awardListMock)
        assert result is True # first checking that the write returned true like the function specifies
        # now checking that the client contains the item that was written in, with user1 and award1 as the keys
        response = client.get_item(TableName = "test_table", 
            Key={
                "userId": {"S":"user1"}, 
                "awardId": {"S": "award1"}
            }
        )
        item = response.get("Item")
        assert item["userId"]["S"] == "user1"
        assert item["awardId"]["S"] == "award1"



    @mock_aws
    def test_update_user_action_stats(self):
        client = boto3.client('dynamodb')
        awardListMock = [ACTION_TYPES.FRIDGE_CLEANED]

        client.create_table(
            TableName = "test_table", 
            KeySchema = [{"AttributeName": "userId", "KeyType": "HASH"}, 
            ],
            AttributeDefinitions = [
                {"AttributeName": "userId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST"
            )
        update_user_action_stats(client, "test_table", "user1", awardListMock)
        update_user_action_stats(client, "test_table", "user1", awardListMock)

        response = client.get_item(TableName = "test_table", 
            Key={
                "userId": {"S":"user1"}
            }
        )

        item = response["Item"]

        expected_total = (ACTION_TYPES.FRIDGE_CLEANED.value["points"] * 2)
        assert int(item["totalPoints"]["N"]) == expected_total

    @mock_aws
    def test_update_user_action_stats_seeds_all_counters(self):
        """All counter fields should be present after the first write, even if
        the corresponding action type was not included in that write."""
        client = boto3.client('dynamodb')
        client.create_table(
            TableName="test_table",
            KeySchema=[{"AttributeName": "userId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "userId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Only write a FRIDGE_CLEANED award — all other counters should still be seeded to 0.
        update_user_action_stats(client, "test_table", "user1", [ACTION_TYPES.FRIDGE_CLEANED])

        item = client.get_item(
            TableName="test_table", Key={"userId": {"S": "user1"}}
        )["Item"]

        for action in ACTION_TYPES:
            counter_field = action.value["action_count_name"]
            assert counter_field in item, f"{counter_field} missing from item"
            if action == ACTION_TYPES.FRIDGE_CLEANED:
                assert int(item[counter_field]["N"]) == 1
            else:
                assert int(item[counter_field]["N"]) == 0, f"{counter_field} should be seeded to 0"

        assert "lastUpdated" in item
        assert item["lastUpdated"]["S"].endswith("Z")

