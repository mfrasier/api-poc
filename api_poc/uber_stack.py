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
        self._vpc = ec2.Vpc.from_lookup(
            self, 'my_vpc',
            vpc_name='MyVPC1'
        )

        self._vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE)

        self._security_group = ec2.SecurityGroup.from_security_group_id(
            self, 'default-sg',
            security_group_id='sg-9d857bf9'
        )

        # TODO someday, create the layer from local zip file
        self._python3_lib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, 'python3-lib-layer',
            layer_version_arn='arn:aws:lambda:us-east-1:011955760856:layer:python3-lib-layer:1'
        )

        # redis cache cluster
        cache_subnet_group = elasticache.CfnSubnetGroup(
            self, 'subnet_group',
            description='elasticache subnet group',
            subnet_ids=['subnet-909a58bb']
        )

        self._redis_cache = elasticache.CfnCacheCluster(
            self, 'cache',
            cache_node_type='cache.t2.micro',
            num_cache_nodes=1,
            engine='redis',
            cache_subnet_group_name=cache_subnet_group.ref,
            vpc_security_group_ids=['sg-9d857bf9'],
        )

        # stack output
        core.CfnOutput(
            self, 'Redis_Address',
            value=self._redis_cache.attr_redis_endpoint_address + ':' +
                  self._redis_cache.attr_redis_endpoint_port
        )

        # external API simulator lambda
        api_handler = _lambda.Function(
            self, "ExternalApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            layers=[self._python3_lib_layer],
            vpc=self._vpc,
            vpc_subnets=self._vpc_subnets,
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

        orchestrator = _lambda.Function(
            self, 'orchestrator',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='orchestrator.handler',
            layers=[self._python3_lib_layer],
            vpc=self._vpc,
            vpc_subnets=self._vpc_subnets,
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
                minute='0/5',
                hour='*',
                month='*',
                week_day='MON-FRI',
                year='*'
            )
        )
        rule.add_target(targets.LambdaFunction(orchestrator))
