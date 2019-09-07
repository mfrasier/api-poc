from aws_cdk import (
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigw,
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    aws_iam as iam,
    core
)

from cdk_watchful import Watchful


class ExternalApi(core.Construct):
    """
    define our external API construct
    """
    # @property
    # def handler(self):
    #     return self.api_handler

    @property
    def redis_address(self):
        return self.redis_cache.attr_redis_endpoint_address

    @property
    def redis_port(self):
        return self.redis_cache.attr_redis_endpoint_port

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        table = dynamodb.Table(
            self, 'throttles',
            partition_key={'name': 'path', 'type': dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        # redis cache cluster
        cache_subnet_group = elasticache.CfnSubnetGroup(
            self, 'subnet_group',
            description='elasticache subnet group',
            subnet_ids=['subnet-909a58bb']
        )

        # defaut_sg = ec2.SecurityGroup.from_security_group_id(
        #     self, 'default_sg',
        #     security_group_id='sg-9d857bf9')
        #
        # defaut_sg.add_ingress_rule(
        #     self,
        #     description='redis',
        #     peer=
        #     connection=
        # )

        self.redis_cache = elasticache.CfnCacheCluster(
            self, 'cache',
            cache_node_type='cache.t2.medium',
            num_cache_nodes=1,
            engine='redis',
            cache_subnet_group_name=cache_subnet_group.ref,
            vpc_security_group_ids=['sg-9d857bf9'],
        )

        # stack output
        core.CfnOutput(
            self, 'Redis_Address',
            value=self.redis_cache.attr_redis_endpoint_address + ':' +
                  self.redis_cache.attr_redis_endpoint_port
        )

        vpc = ec2.Vpc.from_lookup(
            self, 'my_vpc',
            vpc_name='MyVPC1'
        )

        python3_lib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, 'python3-lib-layer',
            layer_version_arn='arn:aws:lambda:us-east-1:011955760856:layer:python3-lib-layer:1'
        )

        # external API simulator lambda
        api_handler = _lambda.Function(
            self, "ExternalApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            layers=[python3_lib_layer],
            tracing=_lambda.Tracing.ACTIVE,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_group=ec2.SecurityGroup.from_security_group_id(
                self, 'default-sg',
                security_group_id='sg-9d857bf9'
            )
        )
        api_handler.add_environment('THROTTLE_TABLE_NAME', table.table_name)
        api_handler.add_environment('REDIS_ADDRESS', self.redis_address)
        api_handler.add_environment('REDIS_PORT', self.redis_port)

        table.grant_read_write_data(api_handler)

        # API Gateway frontend to simulator lambda
        external_gateway = apigw.LambdaRestApi(
            self, 'external_api',
            handler=api_handler,
            proxy=True
        )

        wf = Watchful(self, 'watch')
        # wf.watch_scope(self)
        wf.watch_lambda_function('api_function', api_handler)
