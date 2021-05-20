"""
TODO: turn this into a test suite
"""
from orkestra import compose
import sys
from loguru import logger
import os

logger.add(sys.stderr, serialize=True)

@compose(environment={'foo': 'bar'})
def hello(event):
    logger.bind(environment=os.environ).info('entering hello')
    return f"hello {event}"

@compose
def bye(name):
    return f"bye {name}"

@compose
def double(n):
    return n * 2

@compose
def do(input):
    result = {'hello': 'world'}
    logger.bind(input=input).info(f"{result = }")
    return result

@compose
def derp():
    result = 1 / 0
    return result

# print(hello('event'))

# hello >> bye >> double

# bye >> do


hello >> [bye, double, derp]  >> do
