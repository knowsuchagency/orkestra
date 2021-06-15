import pytest

from examples.hello_orkestra import Item

from orkestra import generic_context as _generic_context


@pytest.fixture(autouse=True)
def disable_powertools(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "1")
    monkeypatch.setenv("POWERTOOLS_LOG_DEDUPLICATION_DISABLED", "1")


@pytest.fixture
def generic_event():
    return Item.random().dict()


@pytest.fixture(scope="session")
def generic_context():
    return _generic_context
