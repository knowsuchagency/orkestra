#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
from aws_cdk import aws_events as eventbridge
from aws_cdk import aws_events_targets as eventbridge_targets
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

# from composer.schedule import schedule
from composer.constructs import Composer
from lambdas.foo import hello


class ExampleStack(cdk.Stack):
    def __init__(self, scope, *args, **kwargs):
        super().__init__(scope, *args, **kwargs)

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
            self, "exampleStateMachine", definition=definition, tracing_enabled=True
        )

        interval_rule = eventbridge.Rule(
            self,
            "exampleRule",
            description="example interval rule",
            schedule=eventbridge.Schedule.cron(),
        )

        interval_rule.add_target(
            eventbridge_targets.SfnStateMachine(machine=state_machine)
        )

        composer = Composer(self, "exampleComposer", hello)

        interval_rule.add_target(
            eventbridge_targets.SfnStateMachine(
                machine=composer.state_machine
            )
        )



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
