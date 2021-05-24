from orkestra import compose


@compose
def handler(event, context):
    return "hello, world"
