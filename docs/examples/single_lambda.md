Orkestra can be used to simplify the process of deployment lambdas
without necessarily composing them as state machines.

=== "examples/single_lambda.py"

    ```python
    from orkestra import compose


    @compose
    def handler(event, context):
        return "hello, world"
    ```

=== "Infrastructure As Code"

    ```python
    from aws_cdk import core as cdk

    from examples.single_lambda import handler


    class SingleLambda(cdk.Stack):
        """Single lambda deployment example."""

        def __init__(self, scope, id, **kwargs):

            super().__init__(scope, id, **kwargs)

            handler.aws_lambda(self)
    ```
