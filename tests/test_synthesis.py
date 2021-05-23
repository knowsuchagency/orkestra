import pytest

from app import synth


@pytest.mark.slow
def test_synthesis():
    """assert that all the stacks synthesize."""
    synth()
