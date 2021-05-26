import random
from typing import *

from orkestra import compose


@compose
def ones_and_zeros(event, context) -> List[int]:
    return random.choices([0, 1], k=10)


@compose(is_map_job=True)
def divide_by(n: int, context) -> float:
    return 1 / n


@compose
def sum_up(numbers: List[float], context):
    return sum(numbers)


@compose
def times_3(n: Union[int, float], context) -> Union[int, float]:
    assert isinstance(n, (int, float))
    return n * 3


ones_and_zeros >> divide_by >> sum_up >> times_3
