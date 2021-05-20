from pathlib import Path
from typing import *
from random import Random
import string

from orkestra.interfaces import ComposableAdjacencyList
from orkestra.utils import orkestrate

OptionalFn = Optional[Union[Callable, List[Callable]]]

random = Random(0)


def sample(k=4):
    return random.sample(string.hexdigits, k)


class Compose:
    def __init__(self, func: OptionalFn = None, context=False, **metadata):
        self.func = func
        self.downstream = []
        self.metadata = metadata
        self.context = context

        if func and not isinstance(func, list):

            module = func.__module__.split(".")

            self.entry = str(Path(*module).parent)
            self.index = Path(*module).name + ".py"
            self.handler = func.__name__

    def __call__(self, event_or_func, context=None):

        if isinstance(self.func, list):
            raise TypeError("can't call a list of functions")

        if self.func is not None:
            event = event_or_func
            if self.context:
                return self.func(event, context)
            else:
                return self.func(event)
        else:
            func = event_or_func
            return self.__class__(func)

    def __repr__(self) -> str:

        if isinstance(self.func, list):
            func = repr(self.func)
        else:
            func = self.func.__name__ if self.func is not None else None

        return (
            "Task("
            f"func={func}, "
            f"metadata={self.metadata}, "
            f"len_downstream={len(self.downstream)}"
            ")"
        )

    def __rshift__(
        self,
        right: Union[ComposableAdjacencyList, List[ComposableAdjacencyList]],
    ):
        right = Compose(func=right) if isinstance(right, list) else right
        self.downstream.append(right)
        return right

    @staticmethod
    def render_lambda(
        composable: "Compose",
        scope,
        id=None,
        function_name=None,
        tracing=None,
        runtime=None,
        dead_letter_queue_enabled=True,
        **kwargs,
    ):

        from aws_cdk import aws_lambda, aws_lambda_python

        id = id or f"{composable.func.__name__}_fn_{sample()}"
        tracing = tracing or aws_lambda.Tracing.ACTIVE
        runtime = runtime or aws_lambda.Runtime.PYTHON_3_8

        keyword_args = dict(
            entry=composable.entry,
            handler=composable.handler,
            index=composable.index,
            function_name=function_name,
            runtime=runtime,
            tracing=tracing,
            dead_letter_queue_enabled=dead_letter_queue_enabled,
        )

        keyword_args.update(kwargs)

        return aws_lambda_python.PythonFunction(
            scope,
            id,
            **keyword_args,
        )

    def aws_lambda(
        self,
        scope,
        id=None,
        function_name=None,
        tracing=None,
        runtime=None,
        dead_letter_queue_enabled=True,
        **kwargs,
    ):

        return self.render_lambda(
            self,
            scope,
            id=id,
            function_name=function_name,
            tracing=tracing,
            runtime=runtime,
            dead_letter_queue_enabled=dead_letter_queue_enabled,
            **kwargs,
        )

    def task(
        self,
        scope,
        id=None,
        payload_response_only=True,
        function_name=None,
        **kwargs,
    ):

        from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
        from aws_cdk import aws_stepfunctions as sfn

        if not isinstance(self.func, list):

            id = id or self.func.__name__

            lambda_fn = self.aws_lambda(
                scope,
                function_name=function_name,
            )

            keyword_args = dict(
                lambda_function=lambda_fn,
                payload_response_only=payload_response_only,
            )

            keyword_args.update(kwargs)

            return orkestrate(
                sfn_tasks.LambdaInvoke(
                    scope,
                    id,
                    **keyword_args,
                )
            )

        else:

            task = sfn.Parallel(
                scope, "parallelize {}".format([c.func.__name__ for c in self.func])
            )

            for fn in self.func:

                lambda_fn = fn.aws_lambda(scope)

                keyword_args = dict(
                    lambda_function=lambda_fn,
                    payload_response_only=payload_response_only,
                )

                keyword_args.update(kwargs)

                branch = sfn_tasks.LambdaInvoke(
                    scope,
                    fn.func.__name__,
                    **keyword_args,
                )

                task.branch(branch)

            return orkestrate(task)

    def definition(
        self,
        scope,
        definition=None,
    ):

        task = self.task(scope)

        definition = task if definition is None else definition.next(task)

        if self.downstream:
            for c in self.downstream:
                c.definition(scope, definition=definition)

        return definition

    def state_machine(
        self, scope, id=None, tracing_enabled=True, state_machine_name=None, **kwargs
    ):

        from aws_cdk import aws_stepfunctions as sfn

        id = id or f"{self.func.__name__}_sfn_{sample()}"

        return sfn.StateMachine(
            scope,
            id,
            definition=self.definition(scope),
            tracing_enabled=tracing_enabled,
            state_machine_name=state_machine_name,
            **kwargs,
        )

    def schedule(
        self,
        scope,
        id=None,
        expression: Optional[str] = None,
        day: Optional[str] = None,
        hour: Optional[str] = None,
        minute: Optional[str] = None,
        month: Optional[str] = None,
        week_day: Optional[str] = None,
        year: Optional[str] = None,
        function_name=None,
        dead_letter_queue_enabled=True,
        **kwargs,
    ):
        from aws_cdk import aws_events as eventbridge
        from aws_cdk import aws_events_targets as eventbridge_targets

        id = id or f"{self.func.__name__}_sched_{sample()}"

        if expression is not None:
            schedule = eventbridge.Schedule.expression(expression)
        else:
            schedule = eventbridge.Schedule.cron(
                day=day,
                hour=hour,
                minute=minute,
                month=month,
                week_day=week_day,
                year=year,
            )

        rule = eventbridge.Rule(
            scope,
            id,
            schedule=schedule,
            **kwargs,
        )

        if not self.downstream:
            fn = self.aws_lambda(
                scope,
                function_name=function_name,
                dead_letter_queue_enabled=dead_letter_queue_enabled,
            )
            target = eventbridge_targets.LambdaFunction(handler=fn)
        else:
            state_machine = self.state_machine(scope)
            target = eventbridge_targets.SfnStateMachine(machine=state_machine)

        rule.add_target(target)

        return rule


compose = Compose
