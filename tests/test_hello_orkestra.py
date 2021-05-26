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


class TestMethods:
    @staticmethod
    def test_generate_item(generic_event, generic_context):
        generated = generate_item(generic_event, generic_context)
        assert Item(**generated)

    @staticmethod
    def test_add_price(generic_event, generic_context):
        result = add_price(generic_event, generic_context)
        assert result["price"]

    @staticmethod
    def test_copy_item(generic_event, generic_context):
        result = copy_item(generic_event, generic_context)
        assert all(i == generic_event for i in result)

    @staticmethod
    def test_double_price(generic_event, generic_context):
        generic_event["price"] = 1
        result = double_price(generic_event, generic_context)
        assert result["price"] == generic_event["price"] * 2

    @staticmethod
    def test_assert_false(generic_event, generic_context):
        with pytest.raises(AssertionError):
            assert_false(generic_event, generic_context)

    @staticmethod
    def test_do_nothing(generic_event, generic_context):
        assert do_nothing(generic_event, generic_context) is None

    @staticmethod
    def test_say_hello(generic_event, generic_context):
        assert say_hello(generic_event, generic_context)

    @staticmethod
    def test_goodbye(generic_event, generic_context):
        assert say_goodbye(generic_event, generic_context)

    @staticmethod
    def test_random_int(generic_event, generic_context):
        result = random_int(generic_event, generic_context)
        assert isinstance(result, int)

    @staticmethod
    def test_random_float(generic_event, generic_context):
        result = random_float(generic_event, generic_context)
        assert isinstance(result, float)
