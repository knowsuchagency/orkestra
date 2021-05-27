from math import isnan
from typing import *

import pytest
from hypothesis import given, infer, assume
from hypothesis.strategies import lists, floats

from examples.map_job import (
    ones_and_zeros,
    divide_by,
    times_3,
    sum_up,
    filter_division_errors,
    Error,
)


def test_ones_and_zeros(generic_event, generic_context):
    result = ones_and_zeros(generic_event, generic_context)
    assert len(result) > 5 and isinstance(result, list)
    assert all(n in [0, 1] for n in result)


def test_divide_by(generic_event, generic_context):
    numbers = ones_and_zeros(generic_event, generic_context)
    for n in numbers:
        if n == 0:
            with pytest.raises(ZeroDivisionError):
                divide_by(n, generic_context)
        else:
            assert divide_by(n, generic_context)


@given(n=infer)
def test_times_3(n: Union[int, float], generic_context):
    assume(not isnan(n))
    assert times_3(n, generic_context) == n * 3


@given(numbers=lists(floats(min_value=0)))
def test_sum_up(numbers: List[float], generic_context):
    assert sum_up(numbers, generic_context) == sum(numbers)


@given(event=infer)
def test_division_error_filter(event: Union[float, Error], generic_context):
    result = filter_division_errors(event, generic_context)
    if isinstance(event, float):
        assume(not isnan(event))
        assert result == event
    else:
        assert result == 0.0
