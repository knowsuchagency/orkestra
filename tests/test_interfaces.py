import pytest

from orkestra import compose
from orkestra.interfaces import AdjacencyList, Composable


@pytest.fixture
def composed():
    @compose
    def noop(event, context):
        ...

    return noop


def test_composable(composed):
    assert isinstance(composed, Composable)


def test_adjacency_list(composed):
    assert isinstance(composed, AdjacencyList)
