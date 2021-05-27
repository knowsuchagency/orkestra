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


def cdk_patch(kwargs: dict):
    """
    Replace interface elements in kwargs with their cdk counterpart.
    """

    for key, value in kwargs.items():

        if hasattr(value, "cdk_construct"):

            kwargs[key] = value.cdk_construct

    return kwargs


coerce = make_composable
