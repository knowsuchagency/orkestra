import random
from typing import *

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
def generate_ints(event, context):
    return [random.randrange(100) for _ in range(10)]


@compose(is_map_job=True)
def halve(n, context):
    return n / 2


@compose
def generate_floats(event, context):
    return [float(n) for n in range(10)]


@compose(is_map_job=True)
def double(n: Union[int, float], context):
    assert isinstance(n, (int, float))
    return n * 2


make_person >> greet >> noop

# when composed in parallel with a list, the state machine
# will fail immediately when any contained lambda fail

random_int >> [random_shape, random_animal] >> noop

# composing lambdas with a tuple will make it so
# the parallel block finishes and succeeds despite errors

random_food >> (random_animal, random_error) >> noop

generate_ints >> halve >> generate_floats >> double
