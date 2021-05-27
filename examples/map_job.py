import random
from typing import *

from orkestra import compose


class Error(TypedDict):
    Error: str
    Cause: str


@compose
def ones_and_zeros(event, context) -> List[int]:
    return random.choices([0, 1], k=10)


@compose(is_map_job=True, capture_map_errors=True)
def divide_by(n: int, context) -> float:
    return 1 / n


@compose(is_map_job=True)
def filter_division_errors(event: Union[float, Error], context) -> float:
    """
    If event is float return event else sum identity.
    """
    return event if isinstance(event, float) else 0.0


@compose
def sum_up(numbers: List[float], context):
    return sum(numbers)


@compose
def times_3(n: Union[int, float], context) -> Union[int, float]:
    assert isinstance(n, (int, float))
    return n * 3


ones_and_zeros >> divide_by >> filter_division_errors >> sum_up >> times_3
