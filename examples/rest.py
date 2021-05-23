import json
import os
import random
import time
from typing import TypedDict
from uuid import uuid4

import boto3
from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel

from orkestra import compose
from orkestra.interfaces import Duration


class Order(TypedDict):
    id: str
    item: str


class OrderResponse(BaseModel):
    execution_arn: str


ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(root_path=ROOT_PATH)

handler = Mangum(app)

input_order: compose


@compose
def input_order(event, context) -> Order:
    return {
        "id": event.get("id", str(uuid4())),
        "item": random.choice(["bean", "tesla", "moon rock"]),
    }


@compose(timeout=Duration.seconds(13))
def process_order(order: Order, context):
    print(f"processing {order = }")
    time.sleep(10)
    print(f"processed {order = }")
    return order


@app.put("/order/{id}", response_model=OrderResponse)
def order(id: str) -> OrderResponse:
    client = boto3.client("stepfunctions")
    response = client.start_execution(
        stateMachineArn=os.environ["STATE_MACHINE_ARN"],
        input=json.dumps({"id": id}),
        # name="string",
        # traceHeader="string",
    )
    return OrderResponse(execution_arn=response["executionArn"])
