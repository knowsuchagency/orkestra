## Powertools

### requirement.txt

If wanting to use [Powertools](https://awslabs.github.io/aws-lambda-powertools-python/latest/) with your lambdas (recommended), make sure to add it to the lambdas' requirements.txt
files as an optional requirement for Orkestra.

=== "lambda_directory/requirements.txt"

    ```
    orkestra[powertools]>=0.4.3
    ```

### timeout

Using Powertools will increase your lambdas' startup time so you will likely
want to increase your lambdas' timeout duration.

=== "lambda_directory/index.py"

    ```python
    from aws_lambda_powertools import Logger

    from orkestra import compose
    from orkestra.interfaces import Duration

    logger = Logger()


    @compose(enable_powertools=True, timeout=Duration.seconds(6))
    def handler(event, context):
        ...
    ```
