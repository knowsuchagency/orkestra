import random
import sys

from loguru import logger

from orkestra import compose

logger.add(sys.stderr, serialize=True)


def handler(event, context):
    logger.bind(event=event, context=context).info("executing")
    return {"random number": random.randrange(100)}


@compose(function_name="no_context_logger")
def no_context_logger(event):
    logger.bind(event=event).info(
        "this lambda doesn't have a context in its function signature"
    )
    return {}
