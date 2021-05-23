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
