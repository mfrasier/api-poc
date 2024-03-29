import sys

from aws_cdk import (
    aws_lambda as _lambda,
    aws_lambda_event_sources as event_sources,
    aws_apigateway as apigw,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_iam as iam,
    aws_sns_subscriptions as sns_subscriptions,
    aws_events as events,
    aws_events_targets as targets,
    aws_elasticache as elasticache,
    aws_logs as logs,
    core
)
import boto3

# TODO use NAT instance instead of service to save money on single-AZ POC

import yaml

config_file_name = 'api_poc.yaml'


def add_sns_email_subscriptions(sns_topic: core.Construct, subscriptions: dict) -> None:
    """
    add email subscriptions from config file to specified SNS topic
    :param sns_topic: topic to add email subscriptions to
    :param subscriptions: email subscriptions for this topic
    :return:
    """
    for subscription in subscriptions:
        email = subscription.get('email')
        if email:
            format_json = subscription.get('json', False)

            sns_topic.add_subscription(
                sns_subscriptions.EmailSubscription(
                    email_address=email,
                    json=format_json
                )
            )
            print('added sns email subscription {} to topic {}'.format(
                email, sns_topic.node.id), file=sys.stderr)
        else:
            print('email attribute not found in subscription {}'.format(subscription), file=sys.stderr)


def nat_ami():
    """retrieve most recent nat ami"""
    ec2 = boto3.client('ec2')
    response = ec2.describe_images(
        Filters=[
            {
                'Name': 'owner-alias',
                'Values': [
                    'amazon'
                ]
            },
            {
                'Name': 'name',
                'Values': [
                    'amzn-ami-vpc-nat*'
                ]
            }
        ]
    )
    return sorted(response['Images'], key=lambda image: image['CreationDate'], reverse=True)[0]['ImageId']


class UberStack(core.Stack):
    """
    Define cloudformation stack to deploy infrastructure and lambdas
    """
    @property
    def redis_address(self) -> str:
        return self._redis_cache.attr_redis_endpoint_address

    @property
    def redis_port(self) -> str:
        return self._redis_cache.attr_redis_endpoint_port

    def __init__(self, scope: core.Stack, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.poc_config = {'api_poc': dict()}
        self.read_config()

        # shared stuff
        self._vpc = ec2.Vpc(
            self, 'api_poc-vpc',
            cidr = '10.0.0.0/23',
            max_azs=1,
            nat_gateways=1,
        )

        self._private_subnet_selection = self._vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE
        )
        self._security_group = ec2.SecurityGroup.from_security_group_id(
            self, 'default_sg',
            security_group_id=self._vpc.vpc_default_security_group)

        self._security_group.add_ingress_rule(
            description='redis',
            peer=self._security_group,
            connection=ec2.Port.tcp_range(start_port=6379, end_port=6379)
        )

        self._python3_lib_layer = _lambda.LayerVersion(
            self,
            'python3-lib-layer',
            description="python3 module dependencies",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_7, _lambda.Runtime.PYTHON_3_6],
            code=_lambda.Code.from_asset('layers/python3-lib-layer.zip')
        )

        # redis cache cluster
        self._cache_subnet_group = elasticache.CfnSubnetGroup(
            self, 'cache_subnet_group',
            description='elasticache subnet group',
            subnet_ids= self._private_subnet_selection.subnet_ids,
            cache_subnet_group_name='cache-subnet-group'
        )

        self._redis_cache = elasticache.CfnCacheCluster(
            self, 'cache',
            cache_node_type='cache.t2.micro',
            num_cache_nodes=1,
            engine='redis',
            cache_subnet_group_name='cache-subnet-group',
            vpc_security_group_ids=[self._security_group.security_group_id],
        )
        self._redis_cache.add_depends_on(self._cache_subnet_group)

        # external API simulator lambda
        api_handler = _lambda.Function(
            self, "external-api",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            layers=[self._python3_lib_layer],
            vpc=self._vpc,
            vpc_subnets=self._private_subnet_selection,
            security_group=self._security_group,
            log_retention=logs.RetentionDays.FIVE_DAYS,
            tracing=_lambda.Tracing.ACTIVE
        )
        api_handler.add_environment('REDIS_ADDRESS', self.redis_address)
        api_handler.add_environment('REDIS_PORT', self.redis_port)

        # API Gateway frontend to simulator lambda
        self._api_gateway = apigw.LambdaRestApi(
            self, 'external_api',
            description='external API emulator',
            options=apigw.StageOptions(
                stage_name='dev'
            ),
            handler=api_handler,
            proxy=True
        )

        job_dlq = sqs.Queue(
            self, 'job-dlq')

        job_queue = sqs.Queue(
            self, 'job-queue',
            dead_letter_queue=sqs.DeadLetterQueue(
                queue=job_dlq,
                max_receive_count=3
            )
        )

        throttle_event_topic = sns.Topic(
            self,
            'throttle-events-topic'
        )

        self.add_sns_subscriptions(throttle_event_topic)

        worker = _lambda.Function(
            self, 'worker',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='worker.handler',
            layers=[self._python3_lib_layer],
            reserved_concurrent_executions=20,
            timeout=core.Duration.minutes(1),
            vpc=self._vpc,
            vpc_subnets=self._private_subnet_selection,
            security_group=self._security_group,
            log_retention=logs.RetentionDays.FIVE_DAYS,
            tracing=_lambda.Tracing.ACTIVE,
            dead_letter_queue_enabled=False
        )
        worker.add_environment('API_KEY', '212221848ab214821de993a9d')
        worker.add_environment('JOB_QUEUE_URL', job_queue.queue_url)
        worker.add_environment('THROTTLE_EVENTS_TOPIC', throttle_event_topic.topic_arn)
        worker.add_environment('REDIS_ADDRESS', self.redis_address)
        worker.add_environment('REDIS_PORT', self.redis_port)
        job_queue.grant_send_messages(worker)
        throttle_event_topic.grant_publish(worker)

        orchestrator = _lambda.Function(
            self, 'orchestrator',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='orchestrator.handler',
            layers=[self._python3_lib_layer],
            reserved_concurrent_executions=1,
            timeout=core.Duration.minutes(2),
            vpc=self._vpc,
            vpc_subnets=self._private_subnet_selection,
            security_group=self._security_group,
            log_retention=logs.RetentionDays.FIVE_DAYS,
            tracing=_lambda.Tracing.ACTIVE,
        )
        orchestrator.add_environment('API_HOST_URL', self._api_gateway.url)
        orchestrator.add_environment('JOB_QUEUE_URL', job_queue.queue_url)
        orchestrator.add_environment('JOB_DLQ_URL', job_dlq.queue_url)
        orchestrator.add_environment('THROTTLE_EVENTS_TOPIC', throttle_event_topic.topic_arn)
        orchestrator.add_environment('REDIS_ADDRESS', self.redis_address)
        orchestrator.add_environment('REDIS_PORT', self.redis_port)
        orchestrator.add_environment('WORKER_FUNCTION_ARN', worker.function_arn)
        job_queue.grant_consume_messages(orchestrator)
        job_dlq.grant_send_messages(orchestrator)
        throttle_event_topic.grant_publish(orchestrator)
        worker.grant_invoke(orchestrator)

        task_master = _lambda.Function(
            self, 'task_master',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='task_master.handler',
            layers=[self._python3_lib_layer],
            reserved_concurrent_executions=1,
            vpc=self._vpc,
            vpc_subnets=self._private_subnet_selection,
            security_group=self._security_group,
            log_retention=logs.RetentionDays.FIVE_DAYS,
            tracing=_lambda.Tracing.ACTIVE,
        )
        task_master.add_environment('SQS_URL', job_queue.queue_url)
        task_master.add_environment('REDIS_ADDRESS', self.redis_address)
        task_master.add_environment('REDIS_PORT', self.redis_port)
        task_master.add_environment('API_HOST_URL', self._api_gateway.url)
        job_queue.grant_send_messages(task_master)

        slack_notify = _lambda.Function(
            self,
            'slack-notify',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('lambda'),
            handler='slack_notify.lambda_handler',
            log_retention=logs.RetentionDays.FIVE_DAYS,
            tracing=_lambda.Tracing.ACTIVE,
        )
        # lambda uses ssm parameter store to retrieve values
        slack_notify.add_environment('encryptedHookUrlKey', '/api_poc/notify/slack/hook_url')
        slack_notify.add_environment('slackChannelKey', '/api_poc/notify/slack/channel')
        slack_notify.add_environment('notifySlack', 'false')
        slack_notify.add_event_source(event_sources.SnsEventSource(throttle_event_topic))
        slack_notify.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                # TODO fix least privilege
                # actions=['ssm:GetParameter'],
                # resources=['arn:aws:ssm:::parameter/api_poc/notify/slack/*'],
                actions=['ssm:*'],
                resources=['*'],
            )
        )

        # kick off lambda(s) once per interval
        rule = events.Rule(
            self, 'orchestrator_rule',
            schedule=events.Schedule.rate(
                core.Duration.hours(1)
            )
        )
        # See https://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-expressions.html
        rule.add_target(targets.LambdaFunction(orchestrator))
        rule.add_target(targets.LambdaFunction(task_master))

        # stack outputs
        core.CfnOutput(
            self, 'Redis_Address',
            value=self._redis_cache.attr_redis_endpoint_address + ':' +
                  self._redis_cache.attr_redis_endpoint_port
        )

    def read_config(self) -> None:
        """ read configuration file """
        print('reading config from {}'.format(config_file_name), file=sys.stderr)
        try:
            with open(config_file_name) as config_file:
                try:
                    self.poc_config = yaml.safe_load(config_file)
                except yaml.YAMLError as e:
                    print('error parsing config file: {}'.format(e), file=sys.stderr)
        except FileNotFoundError as e:
            print('config file not found: {}'.format(config_file_name), file=sys.stderr)

    def add_sns_subscriptions(self, sns_construct: sns.Topic) -> None:
        """ add subscriptions to sns_topic """
        construct_id = sns_construct.node.id
        topic_config = \
            self.poc_config['api_poc'].get('sns', {})\
                .get(construct_id, {}).get('subscriptions', {})

        add_sns_email_subscriptions(sns_construct, topic_config.get('email', {}))
