from orkestra import compose


@compose(state_machine_type="EXPRESS")
def handler(event, context):
    return "hello, world"
