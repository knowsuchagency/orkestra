
def make_composable(obj):
    def __rshift__(self, other):
        return self.next(other)
    obj.__rshift__  = __rshift__

def extend_instance(obj, cls):
    """Apply mixins to a class instance after creation"""
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (base_cls, cls),{})
