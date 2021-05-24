from typing import TypeVar

T = TypeVar("T")


def rshift(self, right):
    result = self.next(right)
    make_composable(right)
    make_composable(result)
    return result


def make_composable(obj: T) -> T:
    obj.__class__.__rshift__ = rshift
    return obj


def cdk_patch(kwargs: dict, /, *elements: str):
    """
    Replaced interface elements in kwargs with cdk counterpart.
    """

    for e in elements:

        if e in kwargs and hasattr(kwargs[e], "construct"):

            construct = kwargs[e].construct

            kwargs[e] = construct

    return kwargs


coerce = make_composable
