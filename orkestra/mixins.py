import inspect

def rshift(self, right):
    return self.next(right)


class ComposableMixin:
    """Make a Nextable a Composable."""

    def __rshift__(self, right):
        result = rshift(self, right)
        right.__class__.__rshift__ = result.__class__.__rshift__ = rshift
        return result
