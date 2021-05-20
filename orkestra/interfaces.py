import abc
import typing
from typing import Protocol, runtime_checkable


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
