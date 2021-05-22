#!/usr/bin/env python3
import string
from random import Random

from aws_cdk import aws_events as eventbridge
from aws_cdk import aws_events_targets as eventbridge_targets
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from aws_cdk import core as cdk

from examples.orchestration import make_person
from examples.powertools import generate_person
from examples.single_lambda import handler
from orkestra import coerce, compose

random = Random(0)


def id_(s: str):
    unique_postfix = "".join(random.sample(string.hexdigits, 4))
    return f"s_{unique_postfix}"


class SingleLambda(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        fn = handler.aws_lambda(self)


class Airflowish(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        make_person.schedule(self, expression="rate(5 minutes)")


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
