import pytest

from orkestra import compose
from orkestra.interfaces import AdjacencyList, Composable


@pytest.mark.interfaces
class TestInterfaces:
    @compose
    def handler(event, context):
        ...

    def test_composable(self):
        assert isinstance(self.handler, Composable)

    def test_adjacency_list(self):
        assert isinstance(self.handler, AdjacencyList)
