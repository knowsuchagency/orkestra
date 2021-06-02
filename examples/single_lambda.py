from orkestra import compose
from orkestra.interfaces import StateMachineType


@compose(state_machine_type=StateMachineType.EXPRESS)
def handler(event, context):
    return "hello, world"
