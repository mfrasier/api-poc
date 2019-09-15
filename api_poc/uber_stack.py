from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_events as events,
    aws_events_targets as targets,
    aws_elasticache as elasticache,
    core
)

import sys


class UberStack(core.Stack):
    @property
    def redis_address(self) -> str:
        return self._redis_cache.attr_redis_endpoint_address

    @property
    def redis_port(self) -> str:
        return self._redis_cache.attr_redis_endpoint_port

    def __init__(self, scope: core.Stack, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

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

        # TODO someday, create the layer from local zip file
        self._python3_lib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, 'python3-lib-layer',
            layer_version_arn='arn:aws:lambda:us-east-1:011955760856:layer:python3-lib-layer:1'
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

        # stack output
        core.CfnOutput(
            self, 'Redis_Address',
            value=self._redis_cache.attr_redis_endpoint_address + ':' +
                  self._redis_cache.attr_redis_endpoint_port
        )

        # external API simulator lambda
        api_handler = _lambda.Function(
            self, "external-api-handler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            layers=[self._python3_lib_layer],
            vpc=self._vpc,
            vpc_subnets=self._private_subnet_selection,
            security_group=self._security_group,
            tracing=_lambda.Tracing.ACTIVE
        )
        api_handler.add_environment('REDIS_ADDRESS', self.redis_address)
        api_handler.add_environment('REDIS_PORT', self.redis_port)

        # API Gateway frontend to simulator lambda
        self._api_gateway = apigw.LambdaRestApi(
            self, 'external_api',
            handler=api_handler,
            proxy=True
        )

        # job queue
        job_queue = sqs.Queue(
            self, 'job_queue')

        sqs_service_endpoint = ec2.InterfaceVpcEndpoint(
            self, 'sqs-service-endpoint',
            vpc=self._vpc,
            service=ec2.InterfaceVpcEndpointAwsService(name='sqs')
        )

        orchestrator = _lambda.Function(
            self, 'orchestrator-handler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='orchestrator.handler',
            layers=[self._python3_lib_layer],
            reserved_concurrent_executions=1,
            vpc=self._vpc,
            vpc_subnets=self._private_subnet_selection,
            security_group=self._security_group,
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
                minute='0/10',
                hour='*',
                month='*',
                week_day='*',
                year='*'
            )
        )
        rule.add_target(targets.LambdaFunction(orchestrator))
