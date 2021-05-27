## Powertools

### requirement.txt

If wanting to use [Powertools](https://awslabs.github.io/aws-lambda-powertools-python/latest/) with your lambdas (recommended), make sure to add it to the lambdas' requirements.txt
files as an optional requirement for Orkestra.

=== "lambda_directory/requirements.txt"

    ```
    orkestra[powertools]>=0.6.0
    ```

### timeouts

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

## Composition

Let's say we had a 3 part workflow `x >> y >> z`.

At some point we needed to add a task that ran immediately after `y`. Let's call it `g`.

`g` runs after `y` but has no effect on `z`.

### Coming from Airflow

If you're coming from Airflow, you would likely add `g` this way:

```python
x >> y >> z

y >> g
```

![airflow graph](assets/images/airflow_graph.png)

### Orkestra (Step Functions) Graph

Orkestra is built on top of AWS Step Functions which don't allow arbitrarily appending multiple downstream nodes to any
to a given part of the State Machine graph, like Airflow.

In order to achieve a similar result, you must group tasks together like so:

```python
x >> y >> [z, g]
```

![orkestra graph](assets/images/orkestra_graph.png)

### Errors

The issue we run into is in the event of the failure of `g`.

Step Functions halt at the entire state machine at the time an error is first encountered.

Remember we said `z` doesn't depend on `g`. If `g` fails before `z` finishes execution, the entire State Machine will
halt execution and `z` won't run.

To help address this, Orkestra allows you to compose tasks like so:

```python
# notice we use a tuple as opposed to a list here
x >> y >> (z, g)
```

![orkestra error capture](assets/images/orkestra_error_capture_graph.png)

This will automatically create tasks for each parallel job that "swallow" errors.

`g` will still show up as having failed but the error will be forwarded as part of the output
of the parallel job that contains it.

You can then decide what to do with that error in a downstream consumer, whether to log it and continue execution,
fail the state machine, loop back, etc.

## Interfaces

Any function decorated with `compose` will have certain methods that are useful for Infrastructure As Code.

### `compose.aws_lambda(...)`

Returns an instance of https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_lambda_python/PythonFunction.html

This removes some of the boilerplate from having to instantiate the `PythonFunction` itself i.e.

=== "original"

    ```python
    import aws_cdk.aws_lambda as lambda_
    from aws_cdk.aws_lambda_python import PythonFunction

    lambda_fn = PythonFunction(self, "MyFunction",
        entry="./lambda_directory", # required
        index="main.py", # optional, defaults to 'index.py'
        handler="do_something", # optional, defaults to 'handler'
        runtime=lambda_.Runtime.PYTHON_3_6
    )
    ```

=== "shortened"

    ```python
    from lambda_directory.main import do_something

    lambda_fn = do_something.aws_lambda(scope)
    ```

### `compose.task(...)`

This returns a Step Functions Task construct like those in https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_stepfunctions_tasks.html

=== "original"

    ```python
    submit_lambda = PythonFunction(self, "MyFunction",
        entry="path/to/fn",
        index="index.py",
        handler="submit",
        runtime=lambda_.Runtime.PYTHON_3_6
    )

    submit_job = tasks.LambdaInvoke(self, "Submit Job",
        lambda_function=submit_lambda,
        # Lambda's result is in the attribute `Payload`
        output_path="$.Payload"
    )
    ```

=== "shortened"

    ```python
    # we decorated the submit function with compose
    from ... import submit

    submit_lambda = submit.aws_lambda(self)

    submit_job = tasks.LambdaInvoke(self, "Submit Job",
        lambda_function=submit_lambda,
        # Lambda's result is in the attribute `Payload`
        output_path="$.Payload"
    )
    ```

=== "further shortened"

    ```python
    submit_job = submit.task(self)
    ```
