import random
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import *
from typing import TypedDict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

from orkestra import compose, map_job

SERVICE_NAME = "validation_example"


class Person(BaseModel):
    name: str
    age: int


class PersonDict(TypedDict):
    name: str
    age: str


@dataclass
class DummyContext:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = (
        "arn:aws:lambda:eu-west-1:809313241:function:test"
    )
    aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"


tracer = Tracer(service=SERVICE_NAME)

logger = Logger(service=SERVICE_NAME)


@tracer.capture_method
@contextmanager
def wait(seconds) -> int:
    time.sleep(seconds)
    yield seconds


@compose
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


@compose
@event_parser(model=Person)
def greet_person(person: Person, context: LambdaContext) -> str:
    logger.info(person.dict())
    return f"hello {person.name}"


@compose
@tracer.capture_lambda_handler
@event_parser(model=Person)
def dismiss_person(person: Person, context: LambdaContext) -> int:
    logger.info({"person": person, "person_dict": person.dict()})
    seconds = 2
    tracer.put_annotation(key="waiting_for", value=seconds)
    with wait(seconds):
        tracer.put_annotation(key="waited", value=seconds)
    return seconds


@compose
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def generate_numbers(event: list, context: LambdaContext) -> List[int]:
    logger.info("collating", extra={"extra": {"event": event}})
    r = random.Random("".join(map(str, event)))
    return [r.randrange(100) for _ in range(1, r.randrange(1, 100))]


@map_job(comment="halve the numbers")
@compose
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def halve(event: int, _):
    return event / 2


generate_person >> (greet_person, dismiss_person) >> generate_numbers >> halve
