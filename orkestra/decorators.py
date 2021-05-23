import string
from collections import defaultdict
from pathlib import Path
from random import Random
from typing import *

from orkestra.utils import coerce
from orkestra.interfaces import Duration

OptionalFn = Optional[Union[Callable, Iterable[Callable]]]

random = Random(0)

_id_map = defaultdict(lambda: 1)


def _sample(k=4):
    return "".join(random.sample(string.hexdigits, k))


def _incremental_id(id):

    mapped = _id_map[id]

    result = id if mapped == 1 else f"{id}{mapped}"

    _id_map[id] += 1

    return result


class Compose:
    def __init__(
        self,
        func: OptionalFn = None,
        timeout: Optional[Duration] = None,
        **aws_lambda_constructor_kwargs,
    ):
        """
        Container for functions meant to be composed.

        Args:
            func: a function or list or tuple of functions
            timeout: the timeout duration of the lambda
            **aws_lambda_constructor_kwargs: pass directly to sfn.PythonFunction
        """

        self.func = func
        self.downstream = []

        self.timeout = timeout

        self.is_map_job = False
        self.map_constructor_kwargs = {}

        self.aws_lambda_constructor_kwargs = aws_lambda_constructor_kwargs

        if func and not isinstance(func, (list, tuple)):

            module = func.__module__.split(".")

            self.entry = str(Path(*module).parent)
            self.index = Path(*module).name + ".py"
            self.handler = func.__name__

    def __call__(self, event_or_func, context=None):

        if isinstance(self.func, (list, tuple)):
            raise TypeError("can't call a list of functions")

        if self.func is not None:
            event = event_or_func
            return self.func(event, context)
        else:
            func = event_or_func
            return Compose(
                func=func,
                timeout=self.timeout,
                **self.aws_lambda_constructor_kwargs,
            )

    def __repr__(self) -> str:

        if isinstance(self.func, (list, tuple)):
            func = repr(self.func)
        else:
            func = self.func.__name__ if self.func is not None else None

        return (
            "Task("
            f"func={func}, "
            f"aws_lambda_constructor_kwargs={self.aws_lambda_constructor_kwargs}, "
            f"len_downstream={len(self.downstream)}"
            ")"
        )

    def __rshift__(self, right):
        right = (
            Compose(func=right) if isinstance(right, (list, tuple)) else right
        )
        self.downstream.append(right)
        return right

    @staticmethod
    def _render_lambda(
        composable: "Compose",
        scope,
        id=None,
        function_name=None,
        tracing=None,
        runtime=None,
        dead_letter_queue_enabled=False,
        **kwargs,
    ):

        from aws_cdk import aws_lambda, aws_lambda_python

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

        keyword_args.update(composable.aws_lambda_constructor_kwargs)

        id = id or f"{composable.func.__name__}_fn_{_sample()}"

        if composable.timeout is not None:

            keyword_args.update(timeout=composable.timeout.construct)

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
        dead_letter_queue_enabled=False,
        **kwargs,
    ):

        return self._render_lambda(
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

        from aws_cdk import aws_stepfunctions as sfn
        from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

        if self.is_map_job:

            id = id or _incremental_id(self.func.__name__)

            map_kwargs = dict(id=id)

            map_kwargs.update(self.map_constructor_kwargs)

            task = sfn.Map(scope, **map_kwargs)

            lambda_fn = self.aws_lambda(
                scope,
                function_name=function_name,
            )

            keyword_args = dict(
                lambda_function=lambda_fn,
                payload_response_only=payload_response_only,
            )

            invoke_lambda = sfn_tasks.LambdaInvoke(
                scope,
                f"invoke_{id}",
                **keyword_args,
            )

            task.iterator(invoke_lambda)

        elif not isinstance(self.func, (list, tuple)):

            id = id or _incremental_id(self.func.__name__)

            lambda_fn = self.aws_lambda(
                scope,
                function_name=function_name,
            )

            keyword_args = dict(
                lambda_function=lambda_fn,
                payload_response_only=payload_response_only,
            )

            keyword_args.update(kwargs)

            task = sfn_tasks.LambdaInvoke(
                scope,
                id,
                **keyword_args,
            )

        else:

            task = sfn.Parallel(
                scope,
                "parallelize {}".format([c.func.__name__ for c in self.func]),
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
                    _incremental_id(fn.func.__name__),
                    **keyword_args,
                )

                if isinstance(self.func, tuple):

                    branch.add_catch(
                        sfn.Pass(scope, f"{fn.func.__name__}_failed")
                    )

                task.branch(branch)

        return coerce(task)

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
        self,
        scope,
        id=None,
        tracing_enabled=True,
        state_machine_name=None,
        **kwargs,
    ):

        from aws_cdk import aws_stepfunctions as sfn

        id = id or f"{self.func.__name__}_sfn_{_sample()}"

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
        state_machine_name=None,
        dead_letter_queue_enabled=False,
        **kwargs,
    ):
        from aws_cdk import aws_events as eventbridge
        from aws_cdk import aws_events_targets as eventbridge_targets

        id = id or f"{self.func.__name__}_sched_{_sample()}"

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
            state_machine = self.state_machine(
                scope,
                state_machine_name=state_machine_name,
            )
            target = eventbridge_targets.SfnStateMachine(machine=state_machine)

        rule.add_target(target)

        return rule


def map_job(decorated=None, **kwargs):
    def decorator(composed: Compose):
        composed.is_map_job = True
        composed.map_constructor_kwargs = kwargs
        return composed

    if decorated is not None:
        return decorator(decorated)
    else:
        return decorator


compose = Compose
