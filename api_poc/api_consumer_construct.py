from aws_cdk import (
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    core
)

from company_infra_construct import CompanyInfrastructure
from core_infra_construct import CoreInfrastructure


class ApiConsumer(CompanyInfrastructure):
    """api consumer construct"""
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        job_queue = sqs.Queue(
            self, 'job_queue')

        orchestrator = _lambda.Function(
            self, 'orchestrator',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='orchestrator.handler',
            layers=[CompanyInfrastructure.python3_lib_layer],
            vpc=CompanyInfrastructure.vpc,
            vpc_subnets=CompanyInfrastructure.vpc_subnets,
            security_group=CompanyInfrastructure.security_group,
            tracing=_lambda.Tracing.ACTIVE,
        )
        orchestrator.add_environment('SQS_URL', job_queue.queue_url)
        orchestrator.add_environment('REDIS_ADDRESS', self.redis_address)
        orchestrator.add_environment('REDIS_PORT', self.redis_port)

        job_queue.grant_consume_messages(orchestrator)

        # kick off lambda once per interval
        # See https://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-expressions.html
        rule = events.Rule(
            self, 'orchestrator_rule',
            schedule=events.Schedule.cron(
                minute='0/5',
                hour='*',
                month='*',
                week_day='MON-FRI',
                year='*'
            )
        )
        rule.add_target(targets.LambdaFunction(orchestrator))


