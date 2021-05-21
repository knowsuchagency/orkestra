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


coerce = make_composable
