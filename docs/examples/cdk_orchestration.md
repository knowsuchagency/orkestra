So far, we've seen examples of lambdas composed together similar to Airflow operators,
where the composition of those functions is defined in the same module as those functions.

This is simple and intuitive and but there are MANY other powerful operations
that can be composed using AWS Step Function besides lambdas.

!!! info "Example Step Functions Tasks"

    * Containerized [Fargate](https://aws.amazon.com/fargate/?whats-new-cards.sort-by=item.additionalFields.postDateTime&whats-new-cards.sort-order=desc&fargate-blogs.sort-by=item.additionalFields.createdDate&fargate-blogs.sort-order=desc) tasks
        * [ECS](https://aws.amazon.com/ecs/?whats-new-cards.sort-by=item.additionalFields.postDateTime&whats-new-cards.sort-order=desc&ecs-blogs.sort-by=item.additionalFields.createdDate&ecs-blogs.sort-order=desc) tasks
        * EC2 tasks
    * HTTP Calls
    * [DynamoDB](https://aws.amazon.com/dynamodb/) CRUD Operations
    * [EMR](https://aws.amazon.com/emr/?whats-new-cards.sort-by=item.additionalFields.postDateTime&whats-new-cards.sort-order=desc) tasks
    * AWS [Glue](https://aws.amazon.com/glue/?whats-new-cards.sort-by=item.additionalFields.postDateTime&whats-new-cards.sort-order=desc) tasks

!!! info "Step Functions CDK Construct Library Overview"
    https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_stepfunctions/README.html

!!! info "Step Functions Tasks Library Overview"
    https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_stepfunctions_tasks/README.html


## Example

!!! question
    Does Orkestra provide a way of helping us compose [arbitrary step function tasks](https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_stepfunctions_tasks.html)
    more intuitively?

**Yes**, Orkestra has a function `coerce` that takes any object with a `.next` method, such as those in [the cdk step functions library](https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_stepfunctions.html),
and updates them such that calling `object_1 >> object_2` is equivalent to returning `object_1.next(object_2)`.

=== "examples/orchestration.py"

    ```python
    import random
    from typing import *

    from orkestra import compose


    class Person(TypedDict):
        name: str
        age: int


    @compose
    def make_person(event, context) -> Person:

        name = random.choice(["Sam", "Alex", "Jay"])

        age = random.randrange(1, 100)

        return {"name": name, "age": age}


    @compose
    def greet(person: Person, context) -> str:

        name = person["name"]

        return f"Hello, {name}"


    @compose
    def random_int(event, context) -> int:
        return random.randrange(100)


    @compose
    def random_shape(event, context):

        return random.choice(["triangle", "circle", "square"])


    @compose
    def random_animal(event, context):

        return random.choice(["cat", "dog", "goat"])


    @compose
    def noop(event, context):
        return {}


    @compose
    def random_food(event, context):

        return random.choice(["peanuts", "potato", "chicken"])


    @compose
    def random_console(event, context):

        return random.choice(["xbox", "playstation", "nintendo"])


    @compose
    def random_error(event, context):

        error = random.choice([ValueError, TypeError, OSError])

        raise error(random.choice(["pigeon", "ufo", "solar flare"]))


    @compose
    def generate_ints(event, context):
        return [random.randrange(100) for _ in range(10)]


    @compose(is_map_job=True)
    def halve(n, context):
        return n / 2


    @compose
    def generate_floats(event, context):
        return [float(n) for n in range(10)]


    @compose(is_map_job=True)
    def double(n: Union[int, float], context):
        assert isinstance(n, (int, float))
        return n * 2


    make_person >> greet >> noop

    # when composed in parallel with a list, the state machine
    # will fail immediately when any contained lambda fail

    random_int >> [random_shape, random_animal] >> noop

    # composing lambdas with a tuple will make it so
    # the parallel block finishes and succeeds despite errors

    random_food >> (random_animal, random_error) >> noop

    generate_ints >> halve >> generate_floats >> double
    ```
=== "Infrastructure As Code"

    ```python
    from aws_cdk import aws_stepfunctions as sfn
    from aws_cdk import core as cdk

    from examples.orchestration import (
        make_person,
        random_int,
        random_shape,
        random_animal,
    )
    from orkestra import coerce


    class CdkComposition(cdk.Stack):
        def __init__(self, scope, id, **kwargs):
            super().__init__(scope, id, **kwargs)

            make_person.state_machine(
                self,
                state_machine_name="non_scheduled_simple_chain_example",
            )

            task_composition_def = (
                random_int.task(self)
                >> random_shape.task(self)
                >> random_animal.task(self)
            )

            sfn.StateMachine(
                self,
                "composed_task_sfn",
                definition=task_composition_def,
                state_machine_name="cdk_task_composition_example",
            )

            wait_1 = sfn.Wait(
                self,
                "wait1",
                time=sfn.WaitTime.duration(cdk.Duration.seconds(1)),
            )

            simple_coercion_def = (
                coerce(wait_1)
                >> random_int.task(self)
                >> sfn.Succeed(self, "great_success")
            )

            sfn.StateMachine(
                self,
                "simple_coercion_sfn",
                definition=simple_coercion_def,
                state_machine_name="simple_coercion_example",
            )
    ```
