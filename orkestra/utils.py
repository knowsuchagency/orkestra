from orkestra.interfaces import Nextable


def coerce(obj: Nextable) -> Nextable:
    """
    Overload the `__rshift__` operator of obj to call its .next() method and do the same for the object it's called on.

    Args:
        obj: an object with a `.next(self, other)` method

    Returns: obj

    """

    def rshift(self, right):
        result = self.next(right)
        coerce(right)
        coerce(result)
        return result

    obj.__class__.__rshift__ = rshift
    return obj


def _cdk_patch(kwargs: dict):
    """
    Replace interface elements in kwargs with their cdk counterpart.
    """

    for key, value in kwargs.items():

        if hasattr(value, "cdk_construct"):

            kwargs[key] = value.cdk_construct

    return kwargs
