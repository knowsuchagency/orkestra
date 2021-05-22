import random
import string


def random_string(event, context):
    return random.sample(string.hexdigits, 4)


def random_int(event, context):
    return random.randrange(100)


def random_float(event, context):
    return random.randrange(101, 9999) / 100
