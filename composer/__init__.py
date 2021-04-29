from pathlib import Path

class compose:
    def __init__(self, func=None, **metadata):
        self.downstream = []
        self.func = func
        self.metadata = metadata

        if func:

            module = func.__module__.split('.')


            self.entry = str(Path(*module).parent)
            self.index = Path(*module).name + ".py"
            self.handler = func.__name__

    def __repr__(self) -> str:
        func = self.func.__name__ if self.func is not None else None
        return (
            "Task("
            f"func={func}, "
            f"metadata={self.metadata}, "
            f"len_downstream={len(self.downstream)}"
            ")"
        )

    def __call__(self, *args, **kwargs):
        if self.func is not None:
            return self.func(*args, **kwargs)

        func, *_ = args

        return self.__class__(func, **self.metadata)

    def __rshift__(self, right):
        self.downstream.append(right)
        return right
