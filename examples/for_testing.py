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


@compose(
    layers=[
        PythonLayerVersion.from_layer_version_arn(
            "arn:aws:lambda:us-east-2:869241709189:layer:gdal-layer:1"
        ),
    ],
)
def fetch_layer(event, context):
    ...


@compose
def invalid_composition(event, context):
    ...


invalid_composition >> invalid_composition
