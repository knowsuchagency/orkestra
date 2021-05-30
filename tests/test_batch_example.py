from examples.batch_example import banana


def test_banana(generic_event, generic_context):
    assert banana(generic_event, generic_context) == "banana"
