import abc
import typing
from dataclasses import dataclass
from enum import Enum
from operator import methodcaller
from typing import Protocol, runtime_checkable, Union

Number = Union[int, float]


class DurationMetric(Enum):
    days = "days"
    hours = "hours"
    millis = "millis"
    minutes = "minutes"
    seconds = "seconds"


class Runtime(Enum):
    PYTHON_3_8 = "PYTHON_3_8"
    PYTHON_3_7 = "PYTHON_3_7"
    PYTHON_3_6 = "PYTHON_3_6"

    @property
    def construct(self):
        """CDK construct."""
        from aws_cdk import aws_lambda

        return getattr(
            aws_lambda.Runtime,
            self.value,
        )


class LambdaInvocationType(Enum):
    """
    https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_stepfunctions_tasks/LambdaInvocationType.html#aws_cdk.aws_stepfunctions_tasks.LambdaInvocationType
    """

    DRY_RUN = "DRY_RUN"
    EVENT = "EVENT"
    REQUEST_RESPONSE = "REQUEST_RESPONSE"

    def construct(self):
        from aws_cdk.aws_stepfunctions_tasks import LambdaInvocationType

        return getattr(LambdaInvocationType, self.value)


class IntegrationPattern(Enum):
    """
    https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_stepfunctions/IntegrationPattern.html#aws_cdk.aws_stepfunctions.IntegrationPattern
    """

    REQUEST_RESPONSE = "REQUEST_RESPONSE"
    RUN_JOB = "RUN_JOB"
    WAIT_FOR_TASK_TOKEN = "WAIT_FOR_TASK_TOKEN"

    def construct(self):
        from aws_cdk.aws_stepfunctions import IntegrationPattern

        return getattr(IntegrationPattern, self.value)


class Tracing(Enum):
    """
    https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_lambda/Tracing.html#aws_cdk.aws_lambda.Tracing
    """

    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PASS_THROUGH = "PASS_THROUGH"

    def construct(self):
        from aws_cdk.aws_lambda import Tracing

        return getattr(Tracing, self.value)


@dataclass
class Duration:
    unit: DurationMetric
    amount: Number

    @property
    def construct(self):
        """CDK construct."""
        from aws_cdk import core as cdk

        f = methodcaller(self.unit.value, self.amount)
        return f(cdk.Duration)

    @classmethod
    def days(cls, amount: Number):
        return cls(unit=DurationMetric.days, amount=amount)

    @classmethod
    def hours(cls, amount: Number):
        return cls(unit=DurationMetric.hours, amount=amount)

    @classmethod
    def millis(cls, amount: Number):
        return cls(unit=DurationMetric.millis, amount=amount)

    @classmethod
    def minutes(cls, amount: Number):
        return cls(unit=DurationMetric.minutes, amount=amount)

    @classmethod
    def seconds(cls, amount: Number):
        return cls(unit=DurationMetric.seconds, amount=amount)


@runtime_checkable
class Composable(Protocol):
    @abc.abstractmethod
    def __rshift__(self, right):
        ...


@runtime_checkable
class AdjacencyList(Protocol):
    downstream: typing.List[Composable]


@runtime_checkable
class ComposableAdjacencyList(Composable, AdjacencyList, Protocol):
    ...


@runtime_checkable
class Nextable(Protocol):
    def next(self, other):
        ...


@runtime_checkable
class NextableComposable(Composable, Nextable, Protocol):
    ...
