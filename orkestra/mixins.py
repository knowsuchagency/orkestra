from orkestra.utils import make_composable, rshift


class ComposableMixin:
    def __rshift__(self, right):
        result = rshift(self, right)
        make_composable(right)
        make_composable(result)
        return result
