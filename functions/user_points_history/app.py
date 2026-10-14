import base64
import json

import binascii
import json
import os
import boto3
from fridge_info_queries import return_fridge_report_notes

# Include get_ddb_client(), encode_key(), and decode_key() here.

def get_ddb_client():
    """Create a DynamoDB client for AWS or local development."""
    deployment_target = os.getenv("DEPLOYMENT_TARGET", "local")

    if deployment_target == "aws":
        return boto3.client("dynamodb")

    return boto3.client(
        "dynamodb",
        endpoint_url="http://localstack:4566",
    )


dynamodb_client = get_ddb_client()
history_table_name = os.environ["USER_POINTS_HISTORY_TABLE"]


def handler(event, context):
    params = event.get("queryStringParameters") or {}

    try:
        limit = int(params.get("limit", "20"))

        if not 1 <= limit <= 100:
            raise ValueError("Invalid limit")

        start_key = decode_key(params.get("nextToken"))

    except (ValueError, TypeError, binascii.Error):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Provide a limit from 1 to 100 and a valid nextToken"
            }),
        }

    page = return_fridge_report_notes(
        dynamodb_client,
        history_table_name,
        limit=limit,
        last_evaluated_key=start_key,
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "items": page["items"],
            "nextToken": encode_key(page["lastEvaluatedKey"]),
        }, default=str),
    }

def encode_key(key: dict | None) -> str | None:
    if not key:
        return None

    raw = json.dumps(key).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_key(token: str | None) -> dict | None:
    if not token:
        return None

    raw = base64.b64decode(
        token,
        altchars=b"-_",
        validate=True,
    )
    key = json.loads(raw.decode("utf-8"))

    if not isinstance(key, dict) or not key:
        raise ValueError("Invalid pagination token")

    return key