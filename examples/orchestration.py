import random
from typing import TypedDict

from orkestra import compose


class Person(TypedDict):
    name: str
    age: int


@compose
def make_person(event, context) -> Person:
    name = random.choice(["Sam", "Alex", "Jay"])
    age = random.randrange(1, 100)
    return {"name": name, "age": age}


@compose
def greet(person: Person, context) -> Person:
    name = person["name"]
    print(f"Hello, {name}")
    return person


@compose
def dismiss(person: Person, context):
    name = person["name"]
    print(f"Goodbye, {name}")


make_person >> greet >> dismiss
