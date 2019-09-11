from aws_cdk import (
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    core
)


class ApiConsumer(core.Construct):
    """api consumer construct"""
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        job_queue = sqs.Queue(
            self, 'job_queue')

        # TODO create a shared construct with VPC, sg, queue, etc shared infrastructure
        vpc = ec2.Vpc.from_lookup(
            self, 'my_vpc',
            vpc_name='MyVPC1'
        )

        orchestrator = _lambda.Function(
            self, 'orchestrator',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='orchestrator.handler',
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_group=ec2.SecurityGroup.from_security_group_id(
                self, 'default_sg',
                security_group_id='sg-9d857bf9'
            )
        )
        orchestrator.add_environment('SQS_ARN', job_queue.queue_arn)
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


