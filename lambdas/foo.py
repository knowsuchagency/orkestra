"""
TODO: turn this into a test suite
"""
from orkestra import compose

@compose(x='y')
def hello(event):
    return {"event": event}

@compose
def bye(name):
    return f"bye {name}"

@compose(x='y')
def double(n):
    return n * 2

@compose
def do(_):
    return {}

# print(hello('event'))

# hello >> bye >> double

# bye >> do


hello >> [bye, double]  >> do
