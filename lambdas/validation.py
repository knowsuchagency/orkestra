import random
import sys

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from loguru import logger
from pydantic import BaseModel

from orkestra import compose

logger.add(sys.stderr, serialize=True)


class Person(BaseModel):
    name: str
    age: int


@compose
def generate_person(event: dict, context):
    logger.bind(event=event, context=context).info("generating person")
    name = event.get("name", "sam")
    age = event.get("age", random.randrange(100))
    person = Person(
        name,
        age,
    )
    return person.dict()


@compose
@event_parser(model=Person)
def greet_person(person: Person, context: LambdaContext):
    logger.bind(person=person.dict(), context=context).info("greeting person")
    return f"hello {person.name}"


generate_person >> greet_person
