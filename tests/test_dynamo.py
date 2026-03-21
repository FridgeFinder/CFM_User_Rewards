
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
            KeySchema = [{"AttributeName": "user_id", "KeyType": "HASH"}, 
            {"AttributeName": "award_id", "KeyType": "RANGE"}], 
            AttributeDefinitions = [
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "award_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST"

            )

        newReportMock = {
                "fridgeId": "greenpointfridge",
                "epochTimestamp": "1762032699",
                "condition": "cleaned",
                "foodPercentage": 2
            }
        result = write_user_points_history(client, "test_table", "user1", "award1", newReportMock, awardListMock)
        assert result is True # first checking that the write returned true like the function specifies
        # now checking that the client contains the item that was written in, with user1 and award1 as the keys
        response = client.get_item(TableName = "test_table", 
            Key={
                "user_id": {"S":"user1"}, 
                "award_id": {"S": "award1"}
            }
        )
        item = response.get("Item")
        assert item["user_id"]["S"] == "user1"
        assert item["award_id"]["S"] == "award1"