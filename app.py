#!/usr/bin/env python3
import os
import string
from random import Random

from aws_cdk import aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import core as cdk

from examples.orchestration import (
    generate_ints,
    make_person,
    random_food,
    random_int,
    random_shape,
    random_animal,
)
from examples.powertools import generate_person, generate_numbers_2
from examples.rest import handler, input_order
from examples.single_lambda import handler
from orkestra import coerce
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda


random = Random(0)


def id_(s: str):
    unique_postfix = "".join(random.sample(string.hexdigits, 4))
    return f"{s}_{unique_postfix}"


class SingleLambda(cdk.Stack):
    """Single lambda deployment example."""

    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        handler.aws_lambda(self)

        handler.state_machine(
            self, state_machine_name="simple_state_machine_example"
        )


class Airflowish(cdk.Stack):
    """
    In this stack, composition happens in the same module in which the functions are defined, like airflow.
    """

    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        make_person.schedule(
            self,
            expression="rate(5 minutes)",
            state_machine_name="simple_chain_example",
        )

        # every day at 12 UTC

        random_int.schedule(
            self,
            expression="cron(0 12 * * ? *)",
            state_machine_name="simple_parallism_example",
        )

        # top of every hour

        random_food.schedule(
            self,
            minute="0",
            state_machine_name="resilient_parallelism_example",
        )

        # every minute

        generate_ints.schedule(self, state_machine_name="map_job_example")


class CdkComposition(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        make_person.state_machine(
            self, state_machine_name="non_scheduled_simple_chain_example"
        )

        task_composition_def = (
            random_int.task(self)
            >> random_shape.task(self)
            >> random_animal.task(self)
        )

        sfn.StateMachine(
            self,
            "composed_task_sfn",
            definition=task_composition_def,
            state_machine_name="cdk_task_composition_example",
        )

        wait_1 = sfn.Wait(
            self,
            "wait1",
            time=sfn.WaitTime.duration(cdk.Duration.seconds(1)),
        )

        simple_coercion_def = (
            coerce(wait_1)
            >> random_int.task(self)
            >> sfn.Succeed(self, "great_success")
        )

        sfn.StateMachine(
            self,
            "simple_coercion_sfn",
            definition=simple_coercion_def,
            state_machine_name="simple_coercion_example",
        )


class Powertools(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        generate_person.schedule(
            self,
            state_machine_name="powertools_example",
        )

        generate_numbers_2.schedule(
            self, state_machine_name="powertools_example_2"
        )


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

        input_order.schedule(self, state_machine_name="schedule_rest_example")


app = cdk.App()


def synth(app=app):

    Powertools(app, "powertools")

    SingleLambda(app, "singleLambda")

    Airflowish(app, "airflowish")

    CdkComposition(app, "cdkComposition")

    RestExample(app, "rest")

    app.synth()


if __name__ == "__main__":

    synth()
