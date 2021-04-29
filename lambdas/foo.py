"""
TODO: turn this into a test suite
"""
from composer import compose

@compose(foo="bar")
def hello(event):
    return {"hello": event}

@compose
def bye(name):
    return f"bye {name}"

@compose(x='y')
def double(n):
    return n * 2

@compose
def do(_):
    return {}

# print(type(hello))

# print(hello("event"))

# print(f"{hello.metadata = }")

hello >> bye >> double

bye >> do

# print(hello)

# print(f"{hello.func.__module__ = }")
