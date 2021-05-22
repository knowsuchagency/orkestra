#!/usr/bin/env python3
import string
from random import Random

from aws_cdk import core as cdk

from examples.orchestration import (
    generate_ints,
    make_person,
    random_food,
    random_int,
)
from examples.powertools import generate_person
from examples.single_lambda import handler

random = Random(0)


def id_(s: str):
    unique_postfix = "".join(random.sample(string.hexdigits, 4))
    return f"s_{unique_postfix}"


class SingleLambda(cdk.Stack):
    """Single lambda deployment example."""

    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        fn = handler.aws_lambda(self)


class Airflowish(cdk.Stack):
    """
    In this stack, composition happens in the same module in which the functions are defined, like airflow.
    """

    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        make_person.schedule(
            self,
            expression="rate(5 minutes)",
            state_machine_name="simple_chain_example",
        )

        # every day at 12 UTC

        random_int.schedule(
            self,
            expression="cron(0 12 * * ? *)",
            state_machine_name="simple_parallism_example",
        )

        # top of every hour

        random_food.schedule(
            self,
            minute="0",
            state_machine_name="resilient_parallelism_example",
        )

        # every minute

        generate_ints.schedule(self, state_machine_name="map_job_example")


class Powertools(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        generate_person.schedule(
            self,
            state_machine_name="powertools_example",
        )


app = cdk.App()

Powertools(app, "powertools")

SingleLambda(app, "singleLambda")

Airflowish(app, "airflowish")


app.synth()
