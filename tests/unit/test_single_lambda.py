from examples.single_lambda import handler


def test_handler():
    assert handler({}, None) == "hello, world"
