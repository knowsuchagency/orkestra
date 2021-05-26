import os
import random
import time
from contextlib import contextmanager
from typing import *
from typing import TypedDict

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
from orkestra import compose, powertools
from pydantic import BaseModel

SERVICE_NAME = "validation_example"

os.environ.setdefault("POWERTOOLS_SERVICE_NAME", SERVICE_NAME)


class Person(BaseModel):
    name: str
    age: int


class PersonDict(TypedDict):
    name: str
    age: str


tracer = Tracer()

logger = Logger()

metrics = Metrics(
    namespace="foo",
    service="bar",
)


@tracer.capture_method
@contextmanager
def wait(seconds) -> int:
    time.sleep(seconds)
    yield seconds


@compose
@powertools
def generate_person(event: dict, context) -> PersonDict:
    logger.info("generating person")
    logger.info("show event as extra", extra={"event": event})
    name = event.get("name", "sam")
    age = event.get("age", random.randrange(100))
    person = Person(
        name=name,
        age=age,
    )
    return person.dict()


@compose(enable_powertools=True, model=Person)
def greet_person(person: Person, context: LambdaContext) -> str:
    logger.info(person.dict())
    return f"hello {person.name}"


@compose
@powertools(model=Person)
def dismiss_person(person: Person, context: LambdaContext) -> int:
    logger.info({"person": person, "person_dict": person.dict()})
    seconds = 2
    tracer.put_metadata(key="waiting_for", value=seconds)
    with wait(seconds):
        tracer.put_metadata(key="waited", value=seconds)
    return seconds


@compose
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def high_five(event, context: LambdaContext):
    logger.info(f"high five {event}")
    seconds = 1
    tracer.put_metadata(key="waiting_for", value=seconds)
    with wait(seconds):
        tracer.put_annotation(key="waited", value=seconds)
    return event


@compose
@powertools
def generate_numbers(event: list, context: LambdaContext) -> List[int]:
    return [random.randrange(100) for _ in range(10)]


@compose(is_map_job=True)
@powertools
def halve(event: int, _):
    return event / 2


@compose(is_map_job=True)
@powertools
def double(n: int, _):
    assert isinstance(n, int)
    return n * 2


generate_numbers_2 = compose(func=generate_numbers.func)


(
    generate_person
    >> high_five
    >> (greet_person, dismiss_person, high_five)
    >> generate_numbers
    >> halve
)

generate_numbers_2 >> double
