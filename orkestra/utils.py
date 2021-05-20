def rshift(self, right):
    return self.next(right)

def make_composable(obj):
    obj.__class__.__rshift__ = rshift
