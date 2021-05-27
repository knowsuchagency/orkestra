from orkestra.decorators import compose, powertools

import pytest


def test_call_list_raises_error(generic_event, generic_context):
    f = compose(func=[])
    with pytest.raises(TypeError, match="can't call a list of functions"):
        f(generic_event, generic_context)


def test_list_compose_repr():
    @compose
    def foo(event, context):
        ...

    f = compose(func=[foo])
    assert repr(f)


def test_powertools_decorator_order():
    with pytest.raises(TypeError):

        @powertools
        @compose
        def f(event, context):
            ...
