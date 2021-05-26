from orkestra import compose


@compose
def hello_world(event, context):
    return "hello, world"


@compose
def invalid_composition(event, context):
    ...


@compose
def g(event, context):
    ...


invalid_composition >> invalid_composition
