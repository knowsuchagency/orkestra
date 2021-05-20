#!/usr/bin/env python3
import os


from aws_cdk import core as cdk
from aws_cdk import aws_events as eventbridge
from aws_cdk import aws_events_targets as eventbridge_targets
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

# from composer.schedule import schedule
from orkestra.constructs import Composer, LambdaInvoke
from lambdas.foo import hello, bye, double, do



class ComposedConstruct(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        definition = hello.task(self) >> bye.task(self) >> double.task(self)

        state_machine = sfn.StateMachine(
            self,
            'composed_sfn_2',
            definition=definition,
            tracing_enabled=True,
            state_machine_name='example_composed_2'
        )


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
            self,
            "exampleStateMachine",
            definition=definition,
            tracing_enabled=True,
            state_machine_name='example_state_machine'
        )

        definition_2 = LambdaInvoke(
            self,
            "exampleLambdaTask3",
            lambda_function=lambda_fn,
            payload_response_only=True,
        ) >> LambdaInvoke(
            self,
            "exampleLambdaTask4",
            lambda_function=lambda_fn,
        )

        state_machine_2 = sfn.StateMachine(
            self,
            "exampleStateMachine2",
            definition=definition_2,
            tracing_enabled=True,
            state_machine_name='example_composed_state_machine'
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
            eventbridge_targets.SfnStateMachine(machine=composer.state_machine)
        )

        ComposedConstruct(self, 'veryComposed')


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
