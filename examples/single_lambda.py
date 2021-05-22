from orkestra import compose


@compose
def handler(event, contex):
    return "hello, world"
