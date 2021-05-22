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


@compose
def say_hello(event, context):

    print("hello")

    return {}


@compose
def random_shape(event, context):

    return random.choice(["triangle", "circle", "square"])


@compose
def random_animal(event, context):

    return random.choice(["cat", "dog", "goat"])


@compose
def noop(event, context):
    return {}


@compose
def random_food(event, context):

    return random.choice(["peanuts", "potato", "chicken"])


@compose
def random_console(event, context):

    return random.choice(["xbox", "playstation", "nintendo"])


@compose
def random_error(event, context):

    error = random.choice([ValueError, TypeError, OSError])

    raise error()


make_person >> greet >> dismiss

say_hello >> [random_shape, random_animal] >> noop

random_food >> (random_console, random_error) >> noop
