from dataclasses import dataclass

import pytest

from examples.rest import input_order, process_order


@pytest.fixture
def context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = (
            "arn:aws:lambda:eu-west-1:809313241:function:test"
        )
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()


@pytest.fixture
def order():
    return {"id": "foo", "item": "hat"}


def test_input_order(order, context):
    result = input_order(order, context)
    assert result["id"] == order["id"]


def test_composition():
    assert process_order in input_order.downstream


@pytest.mark.slow
def test_process_order(order, context):
    assert process_order(order, context) == order
