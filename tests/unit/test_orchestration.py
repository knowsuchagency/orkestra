import pytest

from examples.orchestration import *


def test_make_person():
    assert make_person({}, None)


def test_error():

    with pytest.raises((ValueError, TypeError, OSError)):

        random_error({}, None)


def test_halve():
    n = 2
    assert halve.is_map_job
    assert halve(n, None) == n / 2


def test_double():
    n = 1

    assert double.is_map_job
    assert double(n, None) == n * 2

    with pytest.raises(AssertionError):
        double([0], None)


def test_noop():
    assert not noop({}, None)


def test_composition():

    assert greet in make_person.downstream

    assert noop in greet.downstream

    assert halve in generate_ints.downstream

    assert generate_floats in halve.downstream

    assert double in generate_floats.downstream
