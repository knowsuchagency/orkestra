from orkestra import compose
from orkestra.interfaces import (
    Duration,
    Tracing,
    StateMachineType,
    PythonLayerVersion,
)

timeout_seconds = 10

layers = [PythonLayerVersion(entry="./examples/batch")]


@compose(
    timeout=Duration.seconds(timeout_seconds),
    tracing=Tracing.PASS_THROUGH,
    state_machine_type=StateMachineType.EXPRESS,
    layers=layers,
)
def hello_world(event, context):
    return "hello, world"


@compose
def invalid_composition(event, context):
    ...


invalid_composition >> invalid_composition
