#!/usr/bin/env python3
import os
from typing import Type

from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_batch as batch
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from aws_cdk import core as cdk

from examples.batch_example import banana
from examples.hello_orkestra import generate_item
from examples.map_job import ones_and_zeros
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


CDK_DEFAULT_ACCOUNT = os.getenv("CDK_DEFAULT_ACCOUNT", "")

AWS_ACCESS = os.getenv("AWS_ACCESS", "false").lower().startswith("t")


class SingleLambda(cdk.Stack):
    """Single lambda deployment example."""

    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        self.lmb = handler.aws_lambda(self)

        handler.schedule(
            self,
            state_machine_name="simple_scheduled_state_machine_example",
            expression="rate(1 hour)",
        )

        self.state_machine = handler.state_machine(
            self,
            state_machine_name="simple_state_machine_example",
        )

        handler.state_machine(
            self,
            state_machine_type=sfn.StateMachineType.STANDARD,
            state_machine_name="standard_simple_state_machine_example",
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


class HelloOrkestra(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        generate_item.schedule(
            self,
            expression="rate(5 minutes)",
            state_machine_name="hello_orkestra",
        )


class BatchConstruct(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        assert AWS_ACCESS, "Access to AWS necessary to perform lookup"

        default_vpc = ec2.Vpc.from_lookup(
            self,
            "default_vpc",
            is_default=True,
        )

        compute_resources = batch.ComputeResources(
            vpc=default_vpc,
        )

        compute_environment = batch.ComputeEnvironment(
            self,
            "example_compute_environment",
            compute_resources=compute_resources,
        )

        job_queue = batch.JobQueue(
            self,
            "batch_job_queue",
            compute_environments=[
                batch.JobQueueComputeEnvironment(
                    compute_environment=compute_environment,
                    order=1,
                )
            ],
        )

        job_definition = batch.JobDefinition(
            self,
            "example_job_definition",
            container=batch.JobDefinitionContainer(
                image=ecs.ContainerImage.from_asset("./examples/batch/"),
                vcpus=2,
                memory_limit_mib=8,
            ),
        )

        self.batch_job = sfn_tasks.BatchSubmitJob(
            self,
            "example_batch_job",
            job_definition_arn=job_definition.job_definition_arn,
            job_name="example_batch_job",
            job_queue_arn=job_queue.job_queue_arn,
        )


class BatchExample(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        batch_job = BatchConstruct(self, "batch_construct").batch_job

        self.definition = (
            banana.task(self) >> batch_job >> sfn.Succeed(self, "Success!")
        )

        self.state_machine = sfn.StateMachine(
            self,
            "example_batch_sfn",
            definition=self.definition,
            state_machine_name="example_batch_state_machine",
        )


class MapJob(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        ones_and_zeros.schedule(
            self,
            state_machine_name="map_example",
        )


class App:
    def __init__(self):

        self.app = cdk.App()

        self.env = cdk.Environment(
            account=CDK_DEFAULT_ACCOUNT,
            region=os.getenv(
                "AWS_DEFAULT_REGION",
                "us-east-2",
            ),
        )

        self.hello_orkestra = HelloOrkestra(
            self.app, "helloOrkestra", env=self.env
        )

        self.powertools = Powertools(self.app, "powertools", env=self.env)

        self.single_lambda = SingleLambda(
            self.app, "singleLambda", env=self.env
        )

        self.airflowish = Airflowish(self.app, "airflowish", env=self.env)

        self.cdk_composition = CdkComposition(
            self.app, "cdkComposition", env=self.env
        )

        self.rest = RestExample(self.app, "rest", env=self.env)

        self.map_job = MapJob(self.app, "map", env=self.env)

        if AWS_ACCESS:

            self.batch = BatchExample(self.app, "batch", env=self.env)

        self.added = {}

    def add(self, stack: Type[cdk.Stack], id: str, **kwargs):

        stack_instance = stack(self.app, id, env=self.env, **kwargs)

        self.added[id] = stack_instance

        return stack_instance

    def synth(self):

        return self.app.synth()


if __name__ == "__main__":

    app = App()

    app.synth()
