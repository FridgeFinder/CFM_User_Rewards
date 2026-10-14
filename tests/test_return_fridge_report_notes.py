from unittest.mock import Mock
from boto3.dynamodb.types import TypeSerializer # type: ignore

from fridge_info_queries import return_fridge_report_notes


def test_return_fridge_report_notes():
    items = [
        {
            "awardId": "award-123",
            "points": 10,
            "actionTypes": ["REPORT_FRIDGE"],
            "newReport": {
                "fridgeId": "fridge-123",
                "epochTimestamp": 1728000000,
                "note": "Fridge is stocked",
            },
        },
        {
            "awardId": "award-456",
            "points": 20,
            "actionTypes": ["REPORT_FRIDGE", "RESTOCK"],
            "newReport": {
                "fridgeId": "fridge-456",
                "epochTimestamp": 1728003600,
                "note": "Added fresh vegetables",
            },
        },
        {
            "awardId": "award-789",
            "points": 5,
            "actionTypes": ["REPORT_FRIDGE"],
            "newReport": {
                "fridgeId": "fridge-789",
                "epochTimestamp": 1728007200,
                "note": "Fridge needs cleaning",
            },
        },
    ]

    serializer = TypeSerializer()
    client = Mock()
    client.scan.return_value = {
        "Items": [
            {key: serializer.serialize(value) for key, value in item.items()}
            for item in items
        ]
    }

    result = return_fridge_report_notes(client, "test-history")

    print("result:", result)

    assert len(result["items"]) == 3
    assert result["lastEvaluatedKey"] is None
    client.scan.assert_called_once_with(
        TableName="test-history",
        Limit=20,
    )