## Event Triggers

Orkestra helps with the orchestration of scheduled cron-like tasks,
similar to Airflow, but being built on top of [Step Functions](https://aws.amazon.com/step-functions/)
means workflows can be invoked by any number of events in the AWS Ecosystem.

!!! info "Example Triggers"

    * API Gateway
    * AppSync (GraphQL) mutations
    * SQS
    * SNS
    * MSK
    * EventBridge
    * Lambdas
    * S3 events

## Example

In this example, we'll create a workflow that can be triggered asynchronously an HTTP call to [API Gateway](https://aws.amazon.com/api-gateway/).

!!! info

    We'll write our API using a modern web framework, [FastAPI](https://fastapi.tiangolo.com) which uses type annotations and [pydantic](https://pydantic-docs.helpmanual.io) to produce automatic API
    documentation and json serialization/deserialization.

    We use [Mangum](https://github.com/jordaneremieff/mangum) to handle the translation of API Gateway calls to [ASGI](https://asgi.readthedocs.io/en/latest/) and vice-versa.

    FastAPI is built on top of [Starlette](https://www.starlette.io) which implements the ASGI protocol to transate HTTP to Python objects and vice-versa.

=== "examples/rest.py"

    ```python
    import os
    import random
    import time
    from typing import TypedDict, Optional
    from uuid import uuid4

    import boto3
    from aws_lambda_powertools import Logger, Tracer
    from fastapi import FastAPI
    from mangum import Mangum
    from orkestra import compose
    from orkestra.interfaces import Duration
    from pydantic import BaseModel, Field


    def _random_item():
        return random.choice(["bean", "tesla", "moon rock"])


    class Order(BaseModel):
        id: str = Field(default_factory=uuid4)
        item: str = Field(default_factory=_random_item)

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

        id = event.get("id", str(uuid4()))

        item = event.get("item", _random_item())

        order = Order(
            id=id,
            item=item,
        )

        return order.dict()


    @compose(model=Order, timeout=Duration.seconds(6), enable_powertools=True)
    def process_order(order: Order, context) -> Order.Dict:
        start = time.time()
        time.sleep(3)
        duration = time.time() - start
        tracer.put_metadata("duration", duration)
        logger.info("successfully processed order", extra={"order": order.dict()})
        return order.dict()


    input_order >> process_order


    @app.put("/order/{id}", response_model=OrderResponse)
    def order(id: str, item: Optional[str] = None) -> OrderResponse:

        client = boto3.client("stepfunctions")

        order = Order(id=id, item=item)

        response = client.start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            input=order.json(),
        )

        return OrderResponse(execution_arn=response["executionArn"])
    ```

=== "Infrastructure As Code"

    ```python
    import os

    from aws_cdk import aws_apigateway as apigw
    from aws_cdk import aws_lambda
    from aws_cdk import aws_lambda_python
    from aws_cdk import aws_stepfunctions as sfn
    from aws_cdk import core as cdk

    from examples.rest import input_order


    class RestExample(cdk.Stack):
        def __init__(self, scope, id, **kwargs):

            super().__init__(scope, id, **kwargs)

            state_machine: sfn.StateMachine

            state_machine = input_order.state_machine(
                self,
                state_machine_name="process_order_example",
            )

            cdk.CfnOutput(
                self,
                "rest_invoked_sfn",
                value=state_machine.state_machine_arn,
            )

            stage_name = os.environ["ENVIRONMENT"]

            fn = aws_lambda_python.PythonFunction(
                self,
                "example_api_handler",
                entry="./examples/",
                index="rest.py",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                environment={
                    "STATE_MACHINE_ARN": state_machine.state_machine_arn,
                    "ROOT_PATH": stage_name,
                },
            )

            state_machine.grant_start_execution(fn)

            api = apigw.LambdaRestApi(
                self,
                "example_api",
                handler=fn,
                deploy_options=apigw.StageOptions(stage_name=stage_name),
            )

            fn.add_environment("ROOT_PATH", stage_name)

            # we can still schedule as normal

            input_order.schedule(
                self,
                state_machine_name="schedule_rest_example",
            )
    ```

=== "examples/requirements.txt"

    ```
    orkestra[powertools]>=0.4.3
    fastapi==0.65.1
    mangum==0.11.0
    boto3==1.17.18
    ```
