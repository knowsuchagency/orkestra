import pytest

from examples.rest import input_order, process_order


@pytest.fixture
def order():
    return {"id": "foo", "item": "hat"}


def test_input_order(order, generic_context):
    result = input_order(order, generic_context)
    assert result["id"] == order["id"]


def test_composition():
    assert process_order in input_order.downstream


@pytest.mark.slow
def test_process_order(order, generic_context):
    assert process_order(order, generic_context) == order
