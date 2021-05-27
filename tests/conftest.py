from dataclasses import dataclass

import pytest

from examples.hello_orkestra import Item


@pytest.fixture(autouse=True)
def disable_powertools(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "1")
    monkeypatch.setenv("POWERTOOLS_LOG_DEDUPLICATION_DISABLED", "1")


@pytest.fixture(scope="session")
def generic_context():
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
def generic_event():
    return Item.random().dict()
