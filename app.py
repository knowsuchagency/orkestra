#!/usr/bin/env python3
import string
from random import Random

from aws_cdk import aws_events as eventbridge
from aws_cdk import aws_events_targets as eventbridge_targets
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from aws_cdk import core as cdk

from lambdas.bar import hello as resilient_hello
from lambdas.foo import bye, do, double, hello
from orkestra import coerce

random = Random(0)


def id_(s: str):
    unique_postfix = "".join(random.sample(string.hexdigits, 4))
    return f"s_{unique_postfix}"


class RegularConstruct(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        lambda_fn = aws_lambda_python.PythonFunction(
            self,
            id_("example_function"),
            entry="lambdas/",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        definition = sfn_tasks.LambdaInvoke(
            self,
            id_("example_task"),
            lambda_function=lambda_fn,
            payload_response_only=True,
        ).next(
            sfn_tasks.LambdaInvoke(
                self,
                id_("example_task"),
                lambda_function=lambda_fn,
            )
        )

        state_machine = sfn.StateMachine(
            self,
            id_("example_state_machine"),
            definition=definition,
            tracing_enabled=True,
            state_machine_name="example_state_machine",
        )


class SlightlyMoreComposed(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        lambda_fn = aws_lambda_python.PythonFunction(
            self,
            id_("example_function"),
            entry="lambdas/",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        task_1 = coerce(
            sfn_tasks.LambdaInvoke(
                self,
                id_("example_lambda_task"),
                lambda_function=lambda_fn,
                payload_response_only=True,
            )
        )

        task_2 = sfn_tasks.LambdaInvoke(
            self,
            id_("example_lambda_task"),
            lambda_function=lambda_fn,
        )

        task_3 = sfn_tasks.LambdaInvoke(
            self,
            id_("example_lambda_task"),
            lambda_function=lambda_fn,
        )

        definition = task_1 >> task_2 >> task_3

        sfn.StateMachine(
            self,
            id_("example_state_machine"),
            definition=definition,
            tracing_enabled=True,
            state_machine_name="example_composed_state_machine",
        )


class ComposedConstruct(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        definition = (
            hello.task(self)
            >> bye.task(self)
            >> double.task(self)
            >> do.task(self)
        )

        state_machine = sfn.StateMachine(
            self,
            id_("composed_sfn"),
            definition=definition,
            tracing_enabled=True,
            state_machine_name="simple_composition",
        )


class MoreComposed(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        state_machine = sfn.StateMachine(
            self,
            id_("composed_sfn"),
            definition=hello.definition(self),
            tracing_enabled=True,
            state_machine_name="composed_from_definition",
        )


class UltraComposed(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        hello.state_machine(
            self, state_machine_name="composed_from_state_machine_method"
        )


class ScheduledSfn(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        hello.schedule(self)


class ScheduledLambda(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        do.schedule(self)


class ResilientScheduledSfn(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        resilient_hello.schedule(
            self,
            state_machine_name="scheduled_resilient_parallel_example",
        )


class ExampleStack(cdk.Stack):
    def __init__(self, scope, *args, **kwargs):
        super().__init__(scope, *args, **kwargs)

        RegularConstruct(self, "regular_construct")

        SlightlyMoreComposed(self, "slightly_composed")

        ComposedConstruct(self, "composed")

        MoreComposed(self, "more_composed")

        UltraComposed(self, "ultra_composed")

        ScheduledLambda(self, "scheduled_lambda")

        ScheduledSfn(self, "scheduled_sfn")

        ResilientScheduledSfn(self, "resilient_scheduled_sfn")


app = cdk.App()


ExampleStack(
    app,
    "ExampleOrkestraStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.
    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.
    # env=cdk.Environment(
    #     account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    # ),
    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */
    # env=core.Environment(account='123456789012', region='us-east-1'),
    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)

app.synth()
