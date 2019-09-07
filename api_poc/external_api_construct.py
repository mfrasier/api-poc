from aws_cdk import (
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigw,
    aws_elasticache as elasticache,
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

        # external API simulator lambda
        api_handler = _lambda.Function(
            self, "ExternalApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            tracing=_lambda.Tracing.ACTIVE
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
