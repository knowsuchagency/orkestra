#!/usr/bin/env python3
import os
from enum import Enum

from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_batch as batch
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as cpactions
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda_python
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from aws_cdk import core as cdk
from aws_cdk import pipelines
from aws_cdk.aws_codebuild import BuildEnvironmentVariable

from examples.batch_example import banana
from examples.hello_orkestra import generate_item
from examples.map_job import ones_and_zeros
from examples.orchestration import (
    generate_ints,
    make_person,
    random_food,
    random_int,
    random_shape,
    random_animal,
)
from examples.powertools import generate_person, generate_numbers_2
from examples.rest import handler, input_order
from examples.single_lambda import handler
from orkestra import coerce
from orkestra.utils import _coalesce


class Environment(Enum):
    LOCAL = "LOCAL"
    GITHUB = "GITHUB"
    DEV = "DEV"
    QA = "QA"
    PROD = "PROD"
    CODEBUILD = "CODEBUILD"

    @classmethod
    def from_env(cls):
        env = os.getenv("ENVIRONMENT", "LOCAL")
        return cls[env]

    @property
    @staticmethod
    def pipeline_deployment():
        res = os.getenv("NON_PIPELINE_DEPLOYMENT", "false")

        return res.lower().startswith("t") or res.strip() == "1"


CDK_DEFAULT_ACCOUNT = os.getenv("CDK_DEFAULT_ACCOUNT", "")

ENVIRONMENT = Environment.from_env()

_res = os.getenv("NON_PIPELINE_DEPLOYMENT", "false")

NON_PIPELINE_DEPLOYMENT = _res.lower().startswith("t") or _res.strip() == "1"


def namespace(string: str, namespace=None, environment=None, add_env=False):
    separator = "-"
    namespace = (
        namespace if namespace is not None else os.getenv("NAMESPACE", "")
    )
    environment = (
        environment
        if environment is not None
        else os.getenv("ENVIRONMENT", "")
    )
    strings = [namespace, string]
    if add_env:
        strings.append(environment)
    return separator.join(strings).strip(separator)


class SingleLambda(cdk.Stack):
    """Single lambda deployment example."""

    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        self.lmb = handler.aws_lambda(self)

        handler.schedule(
            self,
            state_machine_name="simple_express_scheduled_state_machine_example",
            expression="rate(1 hour)",
        )

        self.state_machine = handler.state_machine(
            self,
            state_machine_name="simple_express_state_machine_example",
        )

        handler.state_machine(
            self,
            state_machine_type=sfn.StateMachineType.STANDARD,
            state_machine_name="simple_standard_state_machine_example",
        )


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


class CdkComposition(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        make_person.state_machine(
            self, state_machine_name="non_scheduled_simple_chain_example"
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


class Powertools(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        generate_person.schedule(
            self,
            state_machine_name="powertools_example",
        )

        generate_numbers_2.schedule(
            self, state_machine_name="powertools_example_2"
        )


class RestExample(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        state_machine: sfn.StateMachine

        state_machine = input_order.state_machine(
            self,
            state_machine_name="process_order_example",
        )

        cdk.CfnOutput(
            self,
            "rest_invoked_sfn",
            value=state_machine.state_machine_arn,
        )

        stage_name = os.environ["ENVIRONMENT"]

        fn = aws_lambda_python.PythonFunction(
            self,
            "example_api_handler",
            entry="./examples/",
            index="rest.py",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            environment={
                "STATE_MACHINE_ARN": state_machine.state_machine_arn,
                "ROOT_PATH": stage_name,
            },
        )

        state_machine.grant_start_execution(fn)

        api = apigw.LambdaRestApi(
            self,
            "example_api",
            handler=fn,
            deploy_options=apigw.StageOptions(stage_name=stage_name),
        )

        fn.add_environment("ROOT_PATH", stage_name)

        # we can still schedule as normal

        input_order.schedule(self, state_machine_name="schedule_rest_example")


class HelloOrkestra(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        generate_item.schedule(
            self,
            expression="rate(5 minutes)",
            state_machine_name="hello_orkestra",
        )


class BatchConstruct(cdk.Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        assert (
            ENVIRONMENT != Environment.GITHUB
        ), "Access to AWS necessary to perform lookup"

        default_vpc = ec2.Vpc.from_lookup(
            self,
            "default_vpc",
            is_default=True,
        )

        compute_resources = batch.ComputeResources(
            vpc=default_vpc,
        )

        compute_environment = batch.ComputeEnvironment(
            self,
            "example_compute_environment",
            compute_resources=compute_resources,
        )

        job_queue = batch.JobQueue(
            self,
            "batch_job_queue",
            compute_environments=[
                batch.JobQueueComputeEnvironment(
                    compute_environment=compute_environment,
                    order=1,
                )
            ],
        )

        job_definition = batch.JobDefinition(
            self,
            "example_job_definition",
            container=batch.JobDefinitionContainer(
                image=ecs.ContainerImage.from_asset("./examples/batch/"),
                vcpus=2,
                memory_limit_mib=8,
            ),
        )

        self.batch_job = sfn_tasks.BatchSubmitJob(
            self,
            "example_batch_job",
            job_definition_arn=job_definition.job_definition_arn,
            job_name="example_batch_job",
            job_queue_arn=job_queue.job_queue_arn,
        )


class BatchExample(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        batch_job = BatchConstruct(self, "batch_construct").batch_job

        self.definition = (
            banana.task(self) >> batch_job >> sfn.Succeed(self, "Success!")
        )

        self.state_machine = sfn.StateMachine(
            self,
            "example_batch_sfn",
            definition=self.definition,
            state_machine_name="example_batch_state_machine",
        )


class MapJob(cdk.Stack):
    def __init__(self, scope, id, **kwargs):

        super().__init__(scope, id, **kwargs)

        ones_and_zeros.schedule(
            self,
            state_machine_name="map_example",
        )


class Stacks(cdk.Construct):
    """Our collection of stacks."""

    def __init__(self, scope, id, env=None, **kwargs):

        super().__init__(scope, id, **kwargs)

        stack_kwargs = _coalesce({}, env=env)

        self.hello_orkestra = HelloOrkestra(
            self,
            namespace("helloOrkestra"),
            **stack_kwargs,
        )

        self.powertools = Powertools(
            self,
            namespace("powertools"),
            **stack_kwargs,
        )

        self.single_lambda = SingleLambda(
            self,
            namespace("singleLambda"),
            **stack_kwargs,
        )

        self.airflowish = Airflowish(
            self,
            namespace("airflowish"),
            **stack_kwargs,
        )

        self.cdk_composition = CdkComposition(
            self,
            namespace("cdkComposition"),
            **stack_kwargs,
        )

        self.rest = RestExample(
            self,
            namespace("rest"),
            **stack_kwargs,
        )

        self.map_job = MapJob(
            self,
            namespace("map"),
            **stack_kwargs,
        )

        if ENVIRONMENT != Environment.GITHUB:
            self.batch = BatchExample(
                self,
                namespace("batch"),
                **stack_kwargs,
            )


class OrkestraStage(cdk.Stage):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.stacks = Stacks(self, namespace("stacks"))


class PipelineStack(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        source_artifact = codepipeline.Artifact()

        cloud_assembly_artifact = codepipeline.Artifact()

        source_action = cpactions.GitHubSourceAction(
            action_name="GitHub",
            output=source_artifact,
            oauth_token=cdk.SecretValue.secrets_manager("github-token"),
            owner="knowsuchagency",
            repo="orkestra",
            trigger=cpactions.GitHubTrigger.POLL,
            branch="main",
        )

        environment_variables = {
            "POWERTOOLS_TRACE_DISABLED": 1,
            "ENVIRONMENT": "CODEBUILD",
        }

        environment_variables = {
            k: BuildEnvironmentVariable(value=v)
            for k, v in environment_variables.items()
        }

        pipeline = pipelines.CdkPipeline(
            self,
            namespace("cdkPipeline"),
            cloud_assembly_artifact=cloud_assembly_artifact,
            pipeline_name="OrkestraPipeline",
            support_docker_assets=True,
            source_action=source_action,
            synth_action=pipelines.SimpleSynthAction(
                source_artifact=source_artifact,
                cloud_assembly_artifact=cloud_assembly_artifact,
                # install_command="npm install -g aws-cdk && pip install -r requirements.txt",
                # build_command="pytest unittests",
                # synth_command="cdk synth",
                install_commands=[
                    "docker run hello-world",
                    "npm install -g aws-cdk",
                    "pyenv global 3.8.8",
                    "pip install pdm",
                    "head -n 5 pdm.lock",
                    "pdm install -s :all",
                ],
                test_commands=[
                    "pdm run unit-tests",
                ],
                synth_command="pdm run cdk synth",
                environment_variables=environment_variables,
                environment={
                    "privileged": True,
                },
            ),
        )

        self.dev_app = OrkestraStage(
            self,
            "DEV",
            env={
                "account": "869241709189",
                "region": "us-east-2",
            },
        )

        dev_stage = pipeline.add_application_stage(self.dev_app)

        # dev_stage.add_actions(
        #     pipelines.ShellScriptAction(
        #         action_name="Integ",
        #         run_order=dev_stage.next_sequential_run_order(),
        #         additional_artifacts=[source_artifact],
        #         commands=[
        #             "pip install -r requirements.txt",
        #             "pytest integtests",
        #         ],
        #         use_outputs={
        #             "SERVICE_URL": pipeline.stack_output(dev_app.url_output)
        #         },
        #     )
        # )

        dev_stage.add_manual_approval_action()

        pipeline.add_application_stage(
            OrkestraStage(
                self,
                "QA",
                env={
                    "account": "191431834144",
                    "region": "us-east-2",
                },
            )
        )


class OrkestraDeployment(cdk.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        stacks_kwargs = {}

        if kwargs.get("env") is not None:
            stacks_kwargs.update(env=kwargs["env"])

        self.stacks = Stacks(
            self,
            namespace("stacks"),
            **stacks_kwargs,
        )


if __name__ == "__main__":

    app = cdk.App()

    region = os.getenv("CDK_DEFAULT_REGION", "us-east-2")

    env = cdk.Environment(
        region=region,
        account=CDK_DEFAULT_ACCOUNT,
    )

    PipelineStack(app, namespace("Pipeline"), env=env)

    if NON_PIPELINE_DEPLOYMENT:

        OrkestraDeployment(app, namespace("Orkestra"), env=env)

    app.synth()
