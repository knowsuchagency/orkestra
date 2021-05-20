#!/usr/bin/env python3
import os


from aws_cdk import core as cdk
from aws_cdk import aws_events as eventbridge
from aws_cdk import aws_events_targets as eventbridge_targets
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

from lambdas.foo import hello, bye, double, do
from lambdas.bar import hello as resilient_hello
from orkestra import orkestrate


class RegularConstruct(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        lambda_fn = aws_lambda_python.PythonFunction(
            self,
            "exampleFunction",
            entry="lambdas/",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        definition = sfn_tasks.LambdaInvoke(
            self,
            "exampleLambdaTask",
            lambda_function=lambda_fn,
            payload_response_only=True,
        ).next(
            sfn_tasks.LambdaInvoke(
                self,
                "exampleLambdaTask2",
                lambda_function=lambda_fn,
            )
        )

        state_machine = sfn.StateMachine(
            self,
            "exampleStateMachine",
            definition=definition,
            tracing_enabled=True,
            state_machine_name="example_state_machine",
        )


class SlightlyMoreComposed(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        lambda_fn = aws_lambda_python.PythonFunction(
            self,
            "exampleFunction2",
            entry="lambdas/",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            tracing=aws_lambda.Tracing.ACTIVE,
        )

        definition_2 = (
            orkestrate(
                sfn_tasks.LambdaInvoke(
                    self,
                    "exampleLambdaTask3",
                    lambda_function=lambda_fn,
                    payload_response_only=True,
                )
            )
            >> sfn_tasks.LambdaInvoke(
                self,
                "exampleLambdaTask4",
                lambda_function=lambda_fn,
            )
            >> sfn_tasks.LambdaInvoke(
                self,
                "exampleLambdaTask5",
                lambda_function=lambda_fn,
            )
        )

        state_machine_2 = sfn.StateMachine(
            self,
            "exampleStateMachine2",
            definition=definition_2,
            tracing_enabled=True,
            state_machine_name="example_composed_state_machine",
        )


class ComposedConstruct(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        definition = (
            hello.task(self) >> bye.task(self) >> double.task(self) >> do.task(self)
        )

        state_machine = sfn.StateMachine(
            self,
            "composed_sfn_2",
            definition=definition,
            tracing_enabled=True,
            state_machine_name="example_composed_2",
        )


class MoreComposed(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        state_machine = sfn.StateMachine(
            self,
            "composed_sfn_3",
            definition=hello.definition(self),
            tracing_enabled=True,
            state_machine_name="example_composed_3",
        )


class UltraComposed(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        hello.state_machine(self)


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

        resilient_hello.schedule(self)


class ExampleStack(cdk.Stack):
    def __init__(self, scope, *args, **kwargs):
        super().__init__(scope, *args, **kwargs)

        RegularConstruct(self, "regularConstruct")

        SlightlyMoreComposed(self, "almostComposed")

        ComposedConstruct(self, "composed")

        MoreComposed(self, "moreComposed")

        UltraComposed(self, "ultraComposed")

        ScheduledLambda(self, "scheduledLambda")

        ScheduledSfn(self, "scheduledSFN")

        ResilientScheduledSfn(self, "resilientScheduledSfn")


app = cdk.App()


ExampleStack(
    app,
    "ExampleComposerStack",
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
