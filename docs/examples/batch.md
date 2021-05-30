A minimal AWS Batch example.

=== "Business Logic"

    ```python
    from orkestra import compose


    @compose
    def banana(event, context):
        return "banana"
    ```

=== "Infrastructure As Code"

    ```{.py3 hl_lines="19-21"}
    from aws_cdk import aws_batch as batch
    from aws_cdk import aws_ec2 as ec2
    from aws_cdk import aws_ecs as ecs
    from aws_cdk import aws_stepfunctions as sfn
    from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
    from aws_cdk import core as cdk

    from examples.batch_example import banana


    class BatchExample(cdk.Stack):
        def __init__(self, scope, id, **kwargs):
            super().__init__(scope, id, **kwargs)

            batch_job = BatchConstruct(self, "batch_construct").batch_job

            self.lambda_invoke = banana.task(self)

            self.definition = (
                self.lambda_invoke >> batch_job >> sfn.Succeed(self, "Success!")
            )

            self.state_machine = sfn.StateMachine(
                self,
                "example_batch_sfn",
                definition=self.definition,
                state_machine_name="example_batch_state_machine",
            )


    class BatchConstruct(cdk.Construct):
        def __init__(self, scope, id, **kwargs):
            super().__init__(scope, id, **kwargs)

            default_vpc = ec2.Vpc.from_lookup(
                self,
                "default_vpc",
                is_default=True,
            )

            self.compute_resources = batch.ComputeResources(
                vpc=default_vpc,
            )

            self.compute_environment = batch.ComputeEnvironment(
                self,
                "example_compute_environment",
                compute_resources=self.compute_resources,
            )

            self.job_queue = batch.JobQueue(
                self,
                "batch_job_queue",
                compute_environments=[
                    batch.JobQueueComputeEnvironment(
                        compute_environment=self.compute_environment,
                        order=1,
                    )
                ],
            )

            self.job_definition = batch.JobDefinition(
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
                job_definition_arn=self.job_definition.job_definition_arn,
                job_name="example_batch_job",
                job_queue_arn=self.job_queue.job_queue_arn,
            )
    ```

=== "Dockerfile"

    ```dockerfile
    FROM python:3.8-slim

    ENTRYPOINT ["echo"]

    CMD ["hello, world"]
    ```

=== "State Machine Screenshot"

    ![batch example](../assets/images/batch_example_sfn.jpg)
