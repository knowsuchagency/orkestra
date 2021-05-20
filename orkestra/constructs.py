import os
from pathlib import Path
from typing import *
import random
import string

from aws_cdk import core as cdk
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

from orkestra import compose
from orkestra.mixins import ComposableMixin
from orkestra.utils import extend_instance, make_composable

random.seed(0)


Definition = sfn.IChainable


class LambdaInvoke(sfn_tasks.LambdaInvoke, ComposableMixin):
    ...

class Chain(sfn.Chain, ComposableMixin):
    ...



class Composer(cdk.Construct):
    def __init__(
        self,
        scope,
        id,
        start: compose,
        state_machine_name=None,
    ) -> None:
        super().__init__(scope, id)

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
        fn: Union[compose, aws_lambda_python.PythonFunction],
        id=None,
        payload_response_only=True,
        **kwargs,
    ):

        fn = (
            self.render_fn(fn)
            if not isinstance(fn, aws_lambda_python.PythonFunction)
            else fn
        )

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
        def render_task(c: compose):

            return self.render_sfn_lambda_task(
                c,
                c.func.__name__ + "_task",
            )

        if isinstance(composed.func, list):

            task = sfn.Parallel(
                self, "parallelize {}".format([c.func.__name__ for c in composed.func])
            )

            for c in composed.func:
                task.branch(render_task(c))

        else:

            task = render_task(composed)

        if definition is None:
            definition = task
        else:
            definition = definition.next(task)

        if composed.downstream:
            for c in composed.downstream:
                self.render_definition(c, definition)

        return definition
