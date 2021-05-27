import pytest

from examples import powertools as example


@pytest.fixture
def person() -> example.Person:
    return example.Person(name="Sam", age=28)


@pytest.fixture
def event(person):
    return person.dict()


@pytest.mark.powertools
class TestLocal:
    @staticmethod
    def test_generate_person(event, generic_context):
        result = example.generate_person(event, generic_context)
        assert result == event

    @staticmethod
    def test_halve(generic_context):
        assert example.halve.is_map_job
        assert example.halve(4, generic_context) == 2

    @staticmethod
    def test_double(generic_context):
        assert example.double.is_map_job
        assert example.double(2, generic_context) == 4

    @staticmethod
    def test_generate_numbers(event, generic_context):
        numbers = example.generate_numbers(event, generic_context)
        assert isinstance(numbers, list)
        assert all(isinstance(n, int) for n in numbers)

    @staticmethod
    def test_dismiss_person(event, generic_context):
        example.dismiss_person(event, generic_context)

    @staticmethod
    def test_greet_person(event, generic_context):
        assert example.greet_person(event, generic_context)

    @staticmethod
    def test_high_five(event, generic_context):
        assert example.high_five(event, generic_context)
