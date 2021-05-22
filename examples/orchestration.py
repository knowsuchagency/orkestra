import random
from typing import TypedDict

from orkestra import compose, map_job


class Person(TypedDict):
    name: str
    age: int


@compose
def make_person(event, context) -> Person:

    name = random.choice(["Sam", "Alex", "Jay"])

    age = random.randrange(1, 100)

    return {"name": name, "age": age}


@compose
def greet(person: Person, context) -> str:

    name = person["name"]

    return f"Hello, {name}"


@compose
def random_int(event, context) -> int:
    return random.randrange(100)


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

    raise error(random.choice(["pigeon", "ufo", "solar flare"]))


@compose
def generate_numbers(event, context):
    return [random.randrange(100) for _ in range(10)]


@map_job
@compose
def halve(n: int, context):
    return n / 2


make_person >> greet >> noop

# when composed in parallel with a list, the state machine
# will fail immediately when any contained lambda fail

random_int >> [random_shape, random_animal] >> noop

# composing lambdas with a tuple will make it so
# the parallel block finishes and succeeds despite errors

random_food >> (random_animal, random_error) >> noop

generate_numbers >> halve
