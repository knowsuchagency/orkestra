import pytest

from app import synth


@pytest.mark.synthesis
@pytest.mark.slow
def test_synthesis():
    """assert that all the stacks synthesize."""
    synth()
