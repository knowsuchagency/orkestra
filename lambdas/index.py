from loguru import logger
import sys
import random

logger.add(sys.stderr, serialize=True)


def handler(event, context):
    logger.bind(event=event).info("executing")
    return {"random number": random.randrange(100)}
