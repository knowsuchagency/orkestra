import functools
from collections import defaultdict
from pathlib import Path
from typing import *

from orkestra.interfaces import (
    Duration,
    Runtime,
    LambdaInvocationType,
    IntegrationPattern,
    Tracing,
    StateMachineType as SfnType,
    PythonLayerVersion,
)
from orkestra.utils import coerce, _coalesce
from orkestra.exceptions import CompositionError


OptionalFn = Optional[Union[Callable, Iterable[Callable]]]


_id_map = defaultdict(lambda: 1)


def _incremental_id(id):

    mapped = _id_map[id]

    result = id if mapped == 1 else f"{id}{mapped}"

    _id_map[id] += 1

    return result


class Compose:
    _powertools_defaults = {
        "log_event": True,
        "capture_response": True,
        "capture_error": True,
        "raise_on_empty_metrics": False,
        "capture_cold_start_metric": True,
    }

    _sfn_task_defaults = {
        "payload_response_only": True,
    }

    @property
    def _aws_lambda_defaults(self):
        from aws_cdk.aws_lambda import Runtime, Tracing

        return {
            "runtime": Runtime.PYTHON_3_8,
            "tracing": Tracing.ACTIVE,
        }

    def __init__(
        self,
        func: OptionalFn = None,
        enable_powertools: bool = False,
        is_map_job: bool = False,
        capture_map_errors: bool = False,
        log_event: Optional[bool] = None,
        capture_response: Optional[bool] = None,
        capture_error: Optional[bool] = None,
        raise_on_empty_metrics: Optional[bool] = None,
        capture_cold_start_metric: Optional[bool] = None,
        default_dimensions: Optional[dict] = None,
        model: Optional["pydantic.BaseModel"] = None,
        envelope: Optional["pydantic.BaseModel"] = None,
        timeout: Optional[Duration] = None,
        runtime: Optional[Runtime] = None,
        layers: Optional[Sequence[PythonLayerVersion]] = None,
        comment: Optional[str] = None,
        input_path: Optional[str] = None,
        items_path: Optional[str] = None,
        max_concurrency: Optional[Union[int, float, None]] = None,
        output_path: Optional[str] = None,
        parameters: Optional[Mapping[str, Any]] = None,
        result_path: Optional[str] = None,
        result_selector: Optional[Mapping[str, Any]] = None,
        client_context: Optional[str] = None,
        invocation_type: Optional[LambdaInvocationType] = None,
        payload_response_only: Optional[bool] = None,
        qualifier: Optional[str] = None,
        retry_on_service_exceptions: Optional[bool] = None,
        heartbeat: Optional[Duration] = None,
        integration_pattern: Optional[IntegrationPattern] = None,
        sfn_timeout: Optional[Duration] = None,
        tracing: Optional[Tracing] = None,
        state_machine_type: Optional[SfnType] = None,
        state_machine_name: Optional[str] = None,
        **aws_lambda_constructor_kwargs,
    ):
        """
        Container for functions meant to be composed.

        Args:
            func: a function or list or tuple of functions
            timeout: the timeout duration of the lambda
            enable_powertools: if true, enables powertools
            log_event: passed to aws_lambda_powertools.Logger
            capture_response: passed to aws_lambda_powertools.Tracer
            capture_error: passed to aws_lambda_powertools.Tracer
            raise_on_empty_metrics: passed to aws_lambda_powertools.Metrics
            capture_cold_start_metric: passed to aws_lambda_powertools.Metrics
            default_dimensions: passed to aws_lambda_powertools.Metrics
            model: passed to aws_lambda_powertools.utilities.parser.event_parser
            envelope: passed to aws_lambda_powertools.utilities.parser.event_parser
            runtime: the python runtime to use for the lambda
            layers: A list of layers to add to the function’s execution environment. You can configure your Lambda function to pull in additional code during initialization in the form of layers. Layers are packages of libraries or other dependencies that can be used by multiple functions. Default: - No layers.
            is_map_job: whether the lambda is a map job
            capture_map_errors: set true to add guarantee successful map job execution
            comment: An optional description for this state. Default: No comment
            input_path: JSONPath expression to select part of the state to be the input to this state. May also be the special value JsonPath.DISCARD, which will cause the effective input to be the empty object {}. Default: $
            items_path:  JSONPath expression to select the array to iterate over. Default: $
            max_concurrency: MaxConcurrency. An upper bound on the number of iterations you want running at once. Default: - full concurrency
            output_path: JSONPath expression to select part of the state to be the output to this state. May also be the special value JsonPath.DISCARD, which will cause the effective output to be the empty object {}. Default: $
            parameters: The JSON that you want to override your default iteration input. Default: $
            result_path: JSONPath expression to indicate where to inject the state’s output. May also be the special value JsonPath.DISCARD, which will cause the state’s input to become its output. Default: $
            result_selector: The JSON that will replace the state’s raw result and become the effective result before ResultPath is applied. You can use ResultSelector to create a payload with values that are static or selected from the state’s raw result. Default: - None
            client_context: Up to 3583 bytes of base64-encoded data about the invoking client to pass to the function. Default: - No context
            invocation_type: Invocation type of the Lambda function. Default: InvocationType.REQUEST_RESPONSE
            payload_response_only: Invoke the Lambda in a way that only returns the payload response without additional metadata. The payloadResponseOnly property cannot be used if integrationPattern, invocationType, clientContext, or qualifier are specified. It always uses the REQUEST_RESPONSE behavior. Default: false
            qualifier:  Version or alias to invoke a published version of the function. You only need to supply this if you want the version of the Lambda Function to depend on data in the state machine state. If not, you can pass the appropriate Alias or Version object directly as the lambdaFunction argument. Default: - Version or alias inherent to the lambdaFunction object.
            retry_on_service_exceptions: Whether to retry on Lambda service exceptions. This handles Lambda.ServiceException, Lambda.AWSLambdaException and Lambda.SdkClientException with an interval of 2 seconds, a back-off rate of 2 and 6 maximum attempts. Default: true
            heartbeat: Timeout for the heartbeat. Default: - None
            integration_pattern: AWS Step Functions integrates with services directly in the Amazon States Language. You can control these AWS services using service integration patterns Default: IntegrationPattern.REQUEST_RESPONSE
            sfn_timeout: Timeout for the state machine. Default: - None
            tracing: Enable AWS X-Ray Tracing for Lambda Function. Default: Tracing.Enabled
            state_machine_type: Type of the state machine. Default: StateMachineType.STANDARD
            state_machine_name: A name for the state machine. Default: A name is automatically generated
            **aws_lambda_constructor_kwargs: pass directly to sfn.PythonFunction

        For cdk params see https://docs.aws.amazon.com/cdk/api/latest/python/modules.html
        For powertools params see https://awslabs.github.io/aws-lambda-powertools-python/latest/
        """

        self.func = func
        self.downstream = []

        self.is_map_job = is_map_job
        self.capture_map_errors = capture_map_errors

        self.aws_lambda_constructor_kwargs = aws_lambda_constructor_kwargs

        self.map_job_kwargs = {
            "comment": comment,
            "input_path": input_path,
            "items_path": items_path,
            "max_concurrency": max_concurrency,
            "output_path": output_path,
            "result_path": result_path,
            "result_selector": result_selector,
            "parameters": parameters,
        }

        self.lambda_invoke_kwargs = _coalesce(
            self._sfn_task_defaults,
            {
                "client_context": client_context,
                "invocation_type": invocation_type,
                "payload_response_only": payload_response_only,
                "retry_on_service_exceptions": retry_on_service_exceptions,
                "heartbeat": heartbeat,
                "integration_pattern": integration_pattern,
                "timeout": sfn_timeout,
                "comment": comment,
                "input_path": input_path,
                "output_path": output_path,
                "result_path": result_path,
                "result_selector": result_selector,
                "qualifier": qualifier,
            },
        )

        self.powertools_kwargs = _coalesce(
            self._powertools_defaults,
            default_dimensions=default_dimensions,
            model=model,
            envelope=envelope,
            log_event=log_event,
            capture_response=capture_response,
            capture_error=capture_error,
            raise_on_empty_metrics=raise_on_empty_metrics,
            capture_cold_start_metric=capture_cold_start_metric,
        )

        self.state_machine_kwargs = {
            "state_machine_type": state_machine_type,
            "state_machine_name": state_machine_name,
        }

        self.aws_lambda_constructor_kwargs.update(
            timeout=timeout,
            runtime=runtime,
            tracing=tracing,
            layers=layers,
        )

        self.enable_powertools = enable_powertools

        self._lambda_function = None

        self._update_metadata()

    def _update_metadata(self):
        if self.func and not isinstance(self.func, (list, tuple)):
            module = self.func.__module__.split(".")
            self.aws_lambda_constructor_kwargs.update(
                entry=str(Path(*module).parent),
                index=Path(*module).name + ".py",
                handler=self.func.__name__,
            )

    def __call__(self, event, context=None):

        if self.func is not None and not callable(self.func):

            raise TypeError(f"{self.func} is not callable")

        if self.func is not None:

            if self.enable_powertools:

                return powertools(
                    decorated=self.func,
                    **self.powertools_kwargs,
                )(event, context)

            else:

                return self.func(event, context)

        else:

            self.func = event

            self._update_metadata()

            return self

    def __repr__(self) -> str:

        if hasattr(self.func, "__name__"):
            func = self.func.__name__
        else:
            func = repr(self.func)

        return f"Compose(func={func})"

    def __rshift__(self, right):
        right = (
            Compose(func=right) if isinstance(right, (list, tuple)) else right
        )
        self.downstream.append(right)
        return right

    @staticmethod
    def _render_lambda(
        composable: "Compose",
        scope,
        id=None,
        **kwargs,
    ):

        from aws_cdk.aws_lambda_python import PythonFunction

        id = id or _incremental_id(composable.func.__name__ + "_fn")

        layers = composable.aws_lambda_constructor_kwargs.get("layers")

        if layers is not None:

            runtime = _coalesce(
                composable._aws_lambda_defaults,
                composable.aws_lambda_constructor_kwargs,
            )["runtime"]

            layers = [
                l.cdk_construct(
                    scope,
                    _incremental_id(f"{id}_layer"),
                    compatible_runtimes=[runtime],
                )
                for l in layers
            ]

            if kwargs.get("layers") is not None:

                kwargs["layers"].extend(layers)

            else:

                kwargs["layers"] = layers

        kwargs = _coalesce(
            composable._aws_lambda_defaults,
            composable.aws_lambda_constructor_kwargs,
            kwargs,
        )

        return PythonFunction(
            scope,
            id,
            **kwargs,
        )

    def aws_lambda(
        self,
        scope: "aws_cdk.core.Construct",
        id: Optional[str] = None,
        **kwargs,
    ):
        """
        Return lambda cdk construct.

        Args:
            scope: cdk construct
            id: construct id
            **kwargs: to be passed to aws_cdk.aws_lambda_python.PythonFunction

        Returns (aws_cdk.aws_lambda_python.PythonFunction): python lambda

        """

        return self._render_lambda(
            self,
            scope,
            id=id,
            **kwargs,
        )

    def task(
        self,
        scope: "aws_cdk.core.Construct",
        id: Optional[str] = None,
        payload_response_only: bool = True,
        function_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Return cdk step function task construct.
        """

        from aws_cdk import aws_stepfunctions as sfn
        from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

        if self.is_map_job:

            id = id or _incremental_id(self.func.__name__)

            map_kwargs = _coalesce(self.map_job_kwargs)

            task = sfn.Map(scope, id, **map_kwargs)

            self.lambda_fn = self.aws_lambda(
                scope,
                function_name=function_name,
            )

            keyword_args = _coalesce(
                self.lambda_invoke_kwargs,
                lambda_function=self.lambda_fn,
                payload_response_only=payload_response_only,
                **kwargs,
            )

            task_id = f"invoke_{id}"

            invoke_lambda = sfn_tasks.LambdaInvoke(
                scope,
                task_id,
                **keyword_args,
            )

            if self.capture_map_errors:
                invoke_lambda.add_catch(
                    sfn.Pass(
                        scope,
                        f"{task_id}_failed",
                    )
                )

            task.iterator(invoke_lambda)

        elif isinstance(self.func, (list, tuple)):

            id = "parallelize " + (
                "".join([c.func.__name__ for c in self.func])
            )

            task = sfn.Parallel(
                scope,
                _incremental_id(id),
            )

            for fn in self.func:

                lambda_fn = fn.aws_lambda(scope)

                keyword_args = _coalesce(
                    self.lambda_invoke_kwargs,
                    lambda_function=lambda_fn,
                    payload_response_only=payload_response_only,
                    **kwargs,
                )

                branch = sfn_tasks.LambdaInvoke(
                    scope,
                    _incremental_id(fn.func.__name__),
                    **keyword_args,
                )

                if isinstance(self.func, tuple):

                    branch.add_catch(
                        sfn.Pass(
                            scope,
                            f"{fn.func.__name__}_failed",
                        )
                    )

                task.branch(branch)

        else:

            id = id or _incremental_id(self.func.__name__)

            self.lambda_fn = self.aws_lambda(
                scope,
                function_name=function_name,
            )

            keyword_args = _coalesce(
                self.lambda_invoke_kwargs,
                lambda_function=self.lambda_fn,
                payload_response_only=payload_response_only,
                **kwargs,
            )

            task = sfn_tasks.LambdaInvoke(
                scope,
                id,
                **keyword_args,
            )

        return coerce(task)

    def definition(
        self,
        scope: "aws_cdk.core.Construct",
        previous_definition: Optional[
            "aws_cdk.aws_stepfunctions.IChainable"
        ] = None,
        previously_composed: Optional["Compose"] = None,
    ):
        """
        Return automagically composed cdk state machine definition.

        Args:
            scope: cdk scope
            previous_definition: the previous definition
            previously_composed: the previously composed

        Returns:

        """
        previously_composed = previously_composed or []

        if self in previously_composed:

            raise CompositionError(
                f"Failed to compose {self}. Composition using >> must be acyclic."
            )

        task = self.task(scope)

        definition = (
            task
            if previous_definition is None
            else previous_definition.next(task)
        )

        if self.downstream:

            for c in self.downstream:

                c.definition(
                    scope,
                    previous_definition=definition,
                    previously_composed=previously_composed + [self],
                )

        return definition

    def state_machine(
        self,
        scope: "aws_cdk.core.Construct",
        id: Optional[str] = None,
        tracing_enabled: bool = True,
        state_machine_name: Optional[str] = None,
        state_machine_type: Optional[
            Union[SfnType, "aws_cdk.aws_stepfunctions.StateMachineType"]
        ] = None,
        **kwargs,
    ):
        """
        Return step functions state machine cdk construct.

        Args:
            scope: cdk scope
            id: cdk id
            tracing_enabled: xray tracing
            state_machine_name: name of state machine
            state_machine_type: express or standard
            **kwargs:

        Returns:

        """

        from aws_cdk.aws_stepfunctions import StateMachine, StateMachineType

        id = id or _incremental_id(f"{self.func.__name__}_sfn")

        state_machine_kwargs = _coalesce(
            self.state_machine_kwargs,
            state_machine_name=state_machine_name,
            state_machine_type=state_machine_type,
            **kwargs,
        )

        return StateMachine(
            scope,
            id,
            definition=self.definition(scope),
            tracing_enabled=tracing_enabled,
            **state_machine_kwargs,
        )

    def schedule(
        self,
        scope: "aws_cdk.core.Construct",
        id: Optional[str] = None,
        expression: Optional[str] = None,
        day: Optional[str] = None,
        hour: Optional[str] = None,
        minute: Optional[str] = None,
        month: Optional[str] = None,
        week_day: Optional[str] = None,
        year: Optional[str] = None,
        state_machine_name: Optional[str] = None,
        state_machine_type: Optional[SfnType] = None,
        **kwargs,
    ) -> tuple:
        """
        Schedule lambda or state machine to run on interval using EventBridge scheduled event rule.

        Args:
            scope: cdk scope
            id: construct id
            expression: interval at which to run. Can be cron expression or CloudWatch rate expression
            day: day of month
            hour: hour of day
            minute: minute of our
            month: month of year
            week_day: week day
            year: year
            state_machine_name: the state machine name, if downstream
            state_machine_type: type of state machine; express or standard
            **kwargs:

        Returns (tuple): EventBridge schedule rule, SFN State Machine

        """
        from aws_cdk import aws_events as eventbridge
        from aws_cdk import aws_events_targets as eventbridge_targets

        id = id or _incremental_id(f"{self.func.__name__}_sched")

        if expression is not None:
            schedule = eventbridge.Schedule.expression(expression)
        else:
            schedule = eventbridge.Schedule.cron(
                day=day,
                hour=hour,
                minute=minute,
                month=month,
                week_day=week_day,
                year=year,
            )

        rule = eventbridge.Rule(
            scope,
            id,
            schedule=schedule,
            **kwargs,
        )

        state_machine = self.state_machine(
            scope,
            state_machine_name=state_machine_name,
            state_machine_type=state_machine_type,
            **kwargs,
        )

        target = eventbridge_targets.SfnStateMachine(machine=state_machine)

        rule.add_target(target)

        return rule, state_machine


def powertools(
    decorated: Optional[Callable] = None,
    log_event: bool = True,
    capture_response: bool = True,
    capture_error: bool = True,
    raise_on_empty_metrics: bool = False,
    capture_cold_start_metric: bool = True,
    default_dimensions: Optional[dict] = None,
    model: Optional["pydantic.BaseModel"] = None,
    envelope: Optional["pydantic.BaseModel"] = None,
):
    """
    AWS lambda powertools shortcut.

    Args:
        decorated: the function being decorated
        log_event: passed to aws_lambda_powertools.Logger
        capture_response: passed to aws_lambda_powertools.Tracer
        capture_error: passed to aws_lambda_powertools.Tracer
        raise_on_empty_metrics: passed to aws_lambda_powertools.Metrics
        capture_cold_start_metric: passed to aws_lambda_powertools.Metrics
        default_dimensions: passed to aws_lambda_powertools.Metrics
        model: passed to aws_lambda_powertools.utilities.parser.event_parser
        envelope: passed to aws_lambda_powertools.utilities.parser.event_parser

    For further descriptions, see https://awslabs.github.io/aws-lambda-powertools-python/latest/
    """

    from aws_lambda_powertools import Logger, Tracer, Metrics
    from aws_lambda_powertools.utilities.parser import parse

    def decorator(func):

        if isinstance(func, Compose):

            raise TypeError(
                f"@powertools decorator must be used BELOW the @compose decorator."
            )

        logger, tracer, metrics = (
            func.__globals__.get(x)
            for x in (
                "logger",
                "tracer",
                "metrics",
            )
        )

        if isinstance(logger, Logger):

            func = logger.inject_lambda_context(
                lambda_handler=func,
                log_event=log_event,
            )

        if isinstance(tracer, Tracer):

            func = tracer.capture_lambda_handler(
                lambda_handler=func,
                capture_response=capture_response,
                capture_error=capture_error,
            )

        if isinstance(metrics, Metrics):

            func = metrics.log_metrics(
                lambda_handler=func,
                capture_cold_start_metric=capture_cold_start_metric,
                raise_on_empty_metrics=raise_on_empty_metrics,
                default_dimensions=default_dimensions,
            )

        if model is not None:

            @functools.wraps(func)
            def mini_decorator(event, context):
                """
                Exists because event_parser expects the function it wraps to be named "handler".
                """

                parsed_event = parse(
                    event=event,
                    model=model,
                    envelope=envelope,
                )

                return func(parsed_event, context)

            return mini_decorator

        return func

    if decorated is not None:
        return decorator(decorated)
    else:
        return decorator


compose = Compose
