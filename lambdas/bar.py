"""
TODO: turn this into a test suite
"""
import os
import sys

from loguru import logger

from orkestra import compose

logger.add(sys.stderr, serialize=True)


@compose(environment={"foo": "bar"})
def hello(event, context):
    logger.bind(environment=os.environ, event=event, context=context).info(
        "entering hello"
    )
    return f"hello {event}"


@compose
def bye(name, _):
    return f"bye {name}"


@compose
def double(n, _):
    return n * 2


@compose
def do(input, _):
    result = {"hello": "world"}
    logger.bind(input=input).info(f"{result = }")
    return result


@compose
def derp(_):
    result = 1 / 0
    return result


hello >> (bye, double, derp) >> do
