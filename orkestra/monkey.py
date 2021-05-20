import orkestra.constructs

from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

def patch():
    sfn.Chain = orkestra.constructs.Chain
    sfn_tasks.LambdaInvoke = orkestra.constructs.LambdaInvoke
