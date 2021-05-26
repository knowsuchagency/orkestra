from operator import methodcaller

import pytest
from aws_cdk import (
    core as cdk,
    aws_lambda_python,
    aws_stepfunctions as sfn,
    aws_lambda,
    aws_stepfunctions_tasks as sfn_tasks,
)

from app import App
from examples.for_testing import invalid_composition
from orkestra import interfaces
from orkestra.exceptions import CompositionError


@pytest.mark.cdk
def test_interfaces():

    for runtime in interfaces.Runtime:
        assert isinstance(
            runtime.construct,
            aws_lambda.Runtime,
        )

    for invocation_type in interfaces.LambdaInvocationType:

        assert isinstance(
            invocation_type.construct,
            sfn_tasks.LambdaInvocationType,
        )

    for integration_pattern in interfaces.IntegrationPattern:

        assert isinstance(
            integration_pattern.construct,
            sfn.IntegrationPattern,
        )

    for t in interfaces.Tracing:

        assert isinstance(t.construct, aws_lambda.Tracing)

    for method in ("days", "hours", "millis", "minutes", "seconds"):

        duration = methodcaller(method, 1)(interfaces.Duration)

        assert isinstance(duration.construct, cdk.Duration)


@pytest.mark.cdk
@pytest.mark.slow
class TestApplication:
    @pytest.fixture(scope="class")
    def app(self):

        return App()

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

    def test_synthesis(self, app):
        """assert that all the stacks synthesize."""
        app.synth()

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
