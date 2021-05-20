from pathlib import Path
from typing import *

from orkestra.interfaces import ComposableAdjacencyList

OptionalFn = Optional[Union[Callable, List[Callable]]]


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

    def aws_lambda(self, scope, id=None, tracing=None, runtime=None, **kwargs):

        from aws_cdk import aws_lambda, aws_lambda_python

        id = id or f"{self.func.__name__}_fn"
        tracing = tracing or aws_lambda.Tracing.ACTIVE
        runtime = runtime or aws_lambda.Runtime.PYTHON_3_8

        keyword_args = dict(
            entry=self.entry,
            handler=self.handler,
            index=self.index,
            runtime=runtime,
            tracing=tracing,
        )

        keyword_args.update(kwargs)

        return aws_lambda_python.PythonFunction(
            scope,
            id,
            **keyword_args,
        )

    def task(self, scope, id=None, payload_response_only=True, **kwargs):
        from orkestra.constructs import LambdaInvoke
        from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

        id = id or self.func.__name__

        lambda_fn = self.aws_lambda(scope)

        keyword_args = dict(
            lambda_function=lambda_fn,
            payload_response_only=payload_response_only,
        )

        keyword_args.update(kwargs)

        return LambdaInvoke(
            scope,
            id,
            **keyword_args,
        )


compose: ComposableAdjacencyList = Compose
