import os
from pathlib import Path
from typing import *

from aws_cdk import core as cdk
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

from composer import compose

Definition = sfn.IChainable


@runtime_checkable
class ComposerInterface(Protocol):
    state_machine: sfn.StateMachine


class Composer(cdk.Construct):
    def __init__(
        self,
        scope,
        id,
        start: compose,
        state_machine_name=None,
    ) -> None:
        super().__init__(scope, id)

        # fn = self.render_fn(start)

        # definition = self.render_sfn_lambda_task(
        #     fn,
        #     start.func.__name__ + "_task",
        # )

        # for composed in start.downstream:
        #     fn = self.render_fn(composed)
        #     task = self.render_sfn_lambda_task(
        #         fn,
        #         composed.func.__name__ + "_task",
        #     )
        #     definition = definition.next(task)

        self.state_machine = sfn.StateMachine(
            self,
            "composedStateMachine",
            definition=self.render_definition(start),
            tracing_enabled=True,
            state_machine_name=state_machine_name,
        )

    def render_fn(
        self,
        composed: compose,
        id=None,
        tracing=aws_lambda.Tracing.ACTIVE,
        runtime=aws_lambda.Runtime.PYTHON_3_8,
        **kwargs,
    ) -> aws_lambda_python.PythonFunction:

        keyword_args = dict(
            entry=composed.entry,
            handler=composed.handler,
            index=composed.index,
            runtime=runtime,
            tracing=tracing,
        )

        keyword_args.update(kwargs)

        return aws_lambda_python.PythonFunction(
            self,
            id or composed.func.__name__,
            **keyword_args,
        )

    def render_sfn_lambda_task(
        self,
        fn: aws_lambda_python.PythonFunction,
        id=None,
        payload_response_only=True,
        **kwargs,
    ):

        keyword_args = dict(
            lambda_function=fn,
            payload_response_only=payload_response_only,
        )

        keyword_args.update(kwargs)

        return sfn_tasks.LambdaInvoke(
            self,
            id or "lambda invoke",
            **keyword_args,
        )

    def render_definition(self, composed: compose, definition=None) -> Definition:

        fn = self.render_fn(composed)
        
        task = self.render_sfn_lambda_task(
            fn,
            composed.func.__name__ + "_task",
        )

        if definition is None:
            definition = task
        else:
            definition = definition.next(task)

        if composed.downstream:
            for c in composed.downstream:
                self.render_definition(c, definition)

        return definition
