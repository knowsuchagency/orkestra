## Why Orkestra?

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

### Compared to Airflow

Orkestra takes inspiration from Airflow in terms of the developer experience it provides for composing workflows
and running them on a schedule.

Since Orkestra is primarily an abstraction layer over AWS Step Functions, it means that you're not limited to scheduling
your workflows based on a time interval (cron) like Airflow. Workflows and be triggered from any number of events available in the AWS ecosystem.

That also means that you don't need to worry about operating and maintaining the persistent infrastructure something
like Airflow runs on i.e. a scheduler, message broker, workers, database etc. All of that operational burden is handled
by AWS at a fraction of the cost of Airflow.

For the cost of simply having a small Airflow cluster running via [MWAA](https://docs.aws.amazon.com/mwaa/latest/userguide/what-is-mwaa.html)
or [Astronomer](https://www.astronomer.io) without any jobs, you could have run hundreds of thousands of Orkestra workflows.

On the other hand, Airflow has a lot of unique utility that Orkestra doesn't provide as simply a convenience layer of Step Functions.

* Airflow's UI is unmatched in how it provides visibility into the health of previous executions of the same job.
* Airflow collates the logs of various executions of the same job across workers in one place.
* Airflow makes it trivial to run new executions of the same job from its web UI
* Airflow's statefullness and execution context provides a huge amount of utility when needing to run backfills

## Who is Orkestra for?

* teams running on AWS
* teams that are Python-positive
* teams wanting intuitive means of writing both scheduled and event-driven workflows
* those who want to spend more time implementing business logic and less time on ops and managing infrastructure
    * an experience similar to managed Airflow while paying a fraction of the price for something like
      [MWAA](https://docs.aws.amazon.com/mwaa/latest/userguide/what-is-mwaa.html)

## When *not* to use Orkestra

* teams with a larger budgets and many jobs that require backfills (Airflow excels at this)
