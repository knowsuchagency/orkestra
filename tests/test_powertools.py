from dataclasses import dataclass

import pytest

from examples import powertools as example


@pytest.fixture(autouse=True)
def disable_powertools(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "1")
    monkeypatch.setenv("POWERTOOLS_LOG_DEDUPLICATION_DISABLED", "1")


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
def person() -> example.Person:
    return example.Person(name="Sam", age=28)


@pytest.mark.powertools
class TestLocal:
    @staticmethod
    def test_generate_person(context):
        assert example.generate_person({}, context)

    @staticmethod
    def test_halve(context):
        assert example.halve.is_map_job
        assert example.halve(4, context) == 2

    @staticmethod
    def test_double(context):
        assert example.double.is_map_job
        assert example.double(2, context) == 4

    @staticmethod
    def test_generate_numbers(context):
        numbers = example.generate_numbers({}, context)
        assert isinstance(numbers, list)
        assert all(isinstance(n, int) for n in numbers)

    @staticmethod
    def test_dismiss_person(person, context):
        assert example.dismiss_person(person, context)

    @staticmethod
    def test_greet_person(person, context):
        assert example.greet_person(person, context)
