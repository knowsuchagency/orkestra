import os
from operator import methodcaller

import pytest
from aws_cdk import (
    core as cdk,
    aws_lambda_python,
    aws_stepfunctions as sfn,
    aws_lambda,
    aws_stepfunctions_tasks as sfn_tasks,
)
from aws_cdk.cx_api import CloudAssembly

from app import Stacks
from examples.for_testing import (
    invalid_composition,
    hello_world,
    fetch_layer,
)
from orkestra import interfaces
from orkestra.exceptions import CompositionError


def test_hello_world(generic_event, generic_context):
    assert "hello" in hello_world(generic_event, generic_context)


@pytest.mark.cdk
def test_interfaces():

    for runtime in interfaces.Runtime:
        assert isinstance(
            runtime.cdk_construct,
            aws_lambda.Runtime,
        )

    for invocation_type in interfaces.LambdaInvocationType:

        assert isinstance(
            invocation_type.cdk_construct,
            sfn_tasks.LambdaInvocationType,
        )

    for integration_pattern in interfaces.IntegrationPattern:

        assert isinstance(
            integration_pattern.cdk_construct,
            sfn.IntegrationPattern,
        )

    for t in interfaces.Tracing:

        assert isinstance(t.cdk_construct, aws_lambda.Tracing)

    for sfn_type in interfaces.StateMachineType:

        assert isinstance(sfn_type.cdk_construct, sfn.StateMachineType)

    for method in ("days", "hours", "millis", "minutes", "seconds"):

        duration = methodcaller(method, 1)(interfaces.Duration)

        assert isinstance(duration.cdk_construct, cdk.Duration)


@pytest.mark.cdk
@pytest.mark.slow
class TestApplication:
    @pytest.fixture(scope="class")
    def app(self):

        app = cdk.App()

        account = os.getenv("CDK_DEFAULT_ACCOUNT", "")

        region = os.getenv(
            "AWS_DEFAULT_REGION",
            "us-east-2",
        )

        env = cdk.Environment(
            account=account,
            region=region,
        )

        app.stacks = Stacks(app, "stacks", env=env)

        return app

    @pytest.fixture(scope="class")
    def cloud_assembly(self, app) -> CloudAssembly:

        return app.synth()

    def test_lambda_defaults(self, app):

        assert (
            app.stacks.single_lambda.lmb.runtime.to_string()
            == aws_lambda.Runtime.PYTHON_3_8.to_string()
        )

    def test_single_lambda(self, app):

        assert isinstance(
            app.stacks.single_lambda.lmb,
            aws_lambda_python.PythonFunction,
        )

        assert isinstance(
            app.stacks.single_lambda.state_machine,
            sfn.StateMachine,
        )

        assert repr(app.stacks.single_lambda.lmb)

    def test_invalid_composition(self, app):
        class Invalid(cdk.Stack):
            def __init__(self, scope, id, **kwargs):
                super().__init__(scope, id, **kwargs)
                invalid_composition.state_machine(
                    self,
                    "invalid",
                )

        with pytest.raises(CompositionError):

            Invalid(app, "invalidStack")

    def test_nextable(self, app):
        class HasPass(cdk.Stack):
            def __init__(self, scope, id, **kwargs):
                super().__init__(scope, id, **kwargs)
                self.pass_ = sfn.Pass(
                    self,
                    "pass_me",
                )

        stack = HasPass(app, "hasPass")

        assert isinstance(
            stack.pass_,
            interfaces.Nextable,
        )

    @staticmethod
    def test_cdk_patch(app):
        class CdkPatch(cdk.Stack):
            def __init__(self, scope, id, **kwargs):
                super().__init__(scope, id, **kwargs)
                self.lmb = hello_world.aws_lambda(self)

        stack_name = "cdkPatch"

        stack = CdkPatch(app, stack_name, stack_name=stack_name)
        [
            tracing_config
        ] = stack.lmb.node.default_child.tracing_config._delegates

        assert tracing_config.mode == "PassThrough"

    @staticmethod
    def test_state_machine_type(app):
        class StateMachineTest(cdk.Stack):
            def __init__(self, scope, id, **kwargs):
                super().__init__(scope, id, **kwargs)
                self.sm1 = hello_world.state_machine(self)
                self.sm2 = hello_world.state_machine(
                    self,
                    state_machine_type=interfaces.StateMachineType.STANDARD,
                )
                self.sm3 = hello_world.state_machine(
                    self,
                    state_machine_type=sfn.StateMachineType.STANDARD,
                )

                assert (
                    self.sm1.state_machine_type == sfn.StateMachineType.EXPRESS
                )

                assert self.sm2 is not self.sm3
                assert (
                    self.sm2.state_machine_type
                    == sfn.StateMachineType.STANDARD
                )
                assert (
                    self.sm2.state_machine_type == self.sm3.state_machine_type
                )

        stack_name = "stateMachinetest"

        StateMachineTest(app, stack_name)

    @staticmethod
    def test_layers(app):
        class StateMachineTest(cdk.Stack):
            def __init__(self, scope, id, **kwargs):
                super().__init__(scope, id, **kwargs)

                layers = [
                    aws_lambda_python.PythonLayerVersion(
                        self,
                        "exampleLayer",
                        entry="./docs",
                        compatible_runtimes=[
                            aws_lambda.Runtime.PYTHON_3_8,
                        ],
                    )
                ]

                hello_world.aws_lambda(
                    self,
                    "layertestingfn",
                    layers=layers,
                )

                fetch_layer.aws_lambda(self, "fetchLayerTest")

        stack_name = "LayerTestStack"

        StateMachineTest(app, stack_name)
