import os
import time

from fastapi import FastAPI
from mangum import Mangum
import boto3
from dotenv import load_dotenv
from orkestra import compose
from typing import TypedDict
from uuid import uuid4
import random


class Order(TypedDict):
    id: str
    item: str


load_dotenv()

app = FastAPI()

handler = Mangum(app)

input_order: compose


@compose
def input_order(event, context) -> Order:
    return {
        "id": event.get("id", str(uuid4())),
        "item": random.choice(["bean", "tesla", "moon rock"]),
    }


@compose
def process_order(order: Order, context):
    print(f"processing {order = }")
    time.sleep(1)
    print(f"processed {order = }")
    return order


input_order >> process_order


@app.put("/order/{id}")
def order(id: str):
    client = boto3.client("stepfunctions")
    response = client.start_execution(
        stateMachineArn=os.environ["STATE_MACHINE_ARN"],
        name="string",
        input={"id": id},
        # traceHeader="string",
    )
    return response
