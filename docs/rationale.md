# Why Orkestra?

There are a wide array of workflow orchestration tools to choose from.

!!! info "Workflow Orchestration Frameworks"

    * @apache/airflow
    * @PrefectHQ/prefect
    * @dagster-io/dagster
    * @argoproj/argo-workflows
    * @Netflix/metaflow
    * https://cloud.google.com/workflows
    * https://aws.amazon.com/step-functions/
    * ...and so on

These projects (and others) have their own unique value proposition and use-case.

Orkestra itself is built on top of the latter (Step Functions) and the AWS CDK.

## When to use Orkestra

* your team is running on AWS
* your team is Python-positive
* your team wants an intuitive means of writing both scheduled and event-driven workflows
* your team wants to spend more time implementing business logic and less time on ops and managing infrastructure
    * an experience similar to managed Airflow while paying a fraction of the price for something like
      [MWAA](https://docs.aws.amazon.com/mwaa/latest/userguide/what-is-mwaa.html)

## When *not* to use Orkestra

* your team isn't on AWS
* your team isn't comfortable with Python
* your team has a large budget and many jobs that require backfills (Airflow excels at this)
