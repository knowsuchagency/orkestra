from dataclasses import dataclass

import pytest

from examples.hello_orkestra import (
    generate_item,
    add_price,
    copy_item,
    double_price,
    Item,
    assert_false,
    do_nothing,
    say_hello,
    say_goodbye,
    random_int,
    random_float,
)


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
def item():
    return Item.random().dict()


class TestMethods:
    @staticmethod
    def test_generate_item(item, context):
        generated = generate_item(item, context)
        assert Item(**generated)

    @staticmethod
    def test_add_price(item, context):
        result = add_price(item, context)
        assert result["price"]

    @staticmethod
    def test_copy_item(item, context):
        result = copy_item(item, context)
        assert all(i == item for i in result)

    @staticmethod
    def test_double_price(item, context):
        item["price"] = 1
        result = double_price(item, context)
        assert result["price"] == item["price"] * 2

    @staticmethod
    def test_assert_false(item, context):
        with pytest.raises(AssertionError):
            assert_false(item, context)

    @staticmethod
    def test_do_nothing(item, context):
        assert do_nothing(item, context) is None

    @staticmethod
    def test_say_hello(item, context):
        assert say_hello(item, context)

    @staticmethod
    def test_goodbye(item, context):
        assert say_goodbye(item, context)

    @staticmethod
    def test_random_int(item, context):
        result = random_int(item, context)
        assert isinstance(result, int)

    @staticmethod
    def test_random_float(item, context):
        result = random_float(item, context)
        assert isinstance(result, float)
