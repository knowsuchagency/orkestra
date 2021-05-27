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

from app import App
from examples.for_testing import (
    invalid_composition,
    hello_world,
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

    for method in ("days", "hours", "millis", "minutes", "seconds"):

        duration = methodcaller(method, 1)(interfaces.Duration)

        assert isinstance(duration.cdk_construct, cdk.Duration)


@pytest.mark.cdk
@pytest.mark.slow
class TestApplication:
    @pytest.fixture(scope="class")
    def app(self):

        return App()

    @pytest.fixture(scope="class")
    def cloud_assembly(self, app) -> CloudAssembly:

        return app.synth()

    def test_lambda_defaults(self, app):

        assert (
            app.single_lambda.lmb.runtime.to_string()
            == aws_lambda.Runtime.PYTHON_3_8.to_string()
        )

    def test_single_lambda(self, app):

        assert isinstance(
            app.single_lambda.lmb,
            aws_lambda_python.PythonFunction,
        )

        assert isinstance(
            app.single_lambda.state_machine,
            sfn.StateMachine,
        )

        assert repr(app.single_lambda.lmb)

    def test_invalid_composition(self, app):
        class Invalid(cdk.Stack):
            def __init__(self, scope, id):
                super().__init__(scope, id)
                invalid_composition.state_machine(
                    self,
                    "invalid",
                )

        with pytest.raises(CompositionError):
            app.add(
                Invalid,
                "invalidStack",
            )

    def test_nextable(self, app):
        class HasPass(cdk.Stack):
            def __init__(self, scope, id):
                super().__init__(scope, id)
                self.pass_ = sfn.Pass(
                    self,
                    "pass_me",
                )

        stack: HasPass = app.add(HasPass, "hasPass")

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

        stack_name = "cdkPath"

        stack: CdkPatch = app.add(CdkPatch, "cdkPatch", stack_name=stack_name)

        [
            tracing_config
        ] = stack.lmb.node.default_child.tracing_config._delegates

        assert tracing_config.mode == "PassThrough"
