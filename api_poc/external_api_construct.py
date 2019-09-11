from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    core
)

from cdk_watchful import Watchful


class ExternalApi(core.Construct):
    """
    define our external API construct
    """
    @property
    def api_gateway(self):
        return self.api_gateway

    @property
    def redis_address(self):
        return self.redis_cache.attr_redis_endpoint_address

    @property
    def redis_port(self):
        return self.redis_cache.attr_redis_endpoint_port

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # redis cache cluster
        cache_subnet_group = elasticache.CfnSubnetGroup(
            self, 'subnet_group',
            description='elasticache subnet group',
            subnet_ids=['subnet-909a58bb']
        )

        self.redis_cache = elasticache.CfnCacheCluster(
            self, 'cache',
            cache_node_type='cache.t2.small',
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
        api_handler.add_environment('REDIS_ADDRESS', self.redis_address)
        api_handler.add_environment('REDIS_PORT', self.redis_port)

        # API Gateway frontend to simulator lambda
        self.external_gateway = apigw.LambdaRestApi(
            self, 'external_api',
            handler=api_handler,
            proxy=True
        )

        wf = Watchful(self, 'watch')
        # wf.watch_scope(self)
        wf.watch_lambda_function('api_function', api_handler)
