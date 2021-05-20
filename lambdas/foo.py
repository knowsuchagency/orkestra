"""
TODO: turn this into a test suite
"""
from orkestra import compose
import sys
from loguru import logger

logger.add(sys.stderr, serialize=True)

@compose(x='y')
def hello(event):
    return f"hello {event}"

@compose
def bye(name):
    return f"bye {name}"

@compose(x='y')
def double(n):
    return n * 2

@compose
def do(input):
    result = {'hello': 'world'}
    logger.bind(input=input).info(f"{result = }")
    return result

# print(hello('event'))

# hello >> bye >> double

# bye >> do


hello >> [bye, double]  >> do
