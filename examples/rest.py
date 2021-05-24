import os
import random
import time
from typing import TypedDict
from uuid import uuid4

import boto3
from aws_lambda_powertools import Logger, Tracer
from fastapi import FastAPI
from mangum import Mangum
from orkestra import compose
from orkestra.interfaces import Duration
from pydantic import BaseModel, Field


class Order(BaseModel):
    id: str = Field(default_factory=uuid4)
    item: str = Field(
        default_factory=lambda: random.choice(["bean", "tesla", "moon rock"])
    )

    class Dict(TypedDict):
        id: str
        item: str


class OrderResponse(BaseModel):
    execution_arn: str


ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(root_path=ROOT_PATH)

handler = Mangum(app)

logger = Logger()

tracer = Tracer()


@compose(enable_powertools=True)
def input_order(event: dict, context) -> Order.Dict:
    order = Order(
        id=event.get("id", str(uuid4())),
        item=event.get("item", random.choice(["bean", "tesla", "moon rock"])),
    )
    return order.dict()


@compose(model=Order, timeout=Duration.seconds(13), enable_powertools=True)
def process_order(order: Order, context) -> Order.Dict:
    start = time.time()
    time.sleep(10)
    duration = time.time() - start
    tracer.put_metadata("duration", duration)
    logger.info("successfully processed order", extra={"order": order.dict()})
    return order


input_order >> process_order


@app.put("/order/{id}", response_model=OrderResponse)
def order(id: str) -> OrderResponse:

    client = boto3.client("stepfunctions")

    order = Order(id=id)

    response = client.start_execution(
        stateMachineArn=os.environ["STATE_MACHINE_ARN"],
        input=order.json(),
    )

    return OrderResponse(execution_arn=response["executionArn"])
