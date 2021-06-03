import os

import boto3


def test_successful_sfn_execution():
    client = boto3.client("stepfunctions")

    response = client.start_sync_execution(
        stateMachineArn=os.environ["SINGLE_LAMBDA_STATE_MACHINE_ARN"],
    )

    assert response["status"] == "SUCCEEDED"
