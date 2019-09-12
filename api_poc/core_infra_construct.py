from aws_cdk import (
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    aws_elasticache as elasticache,
    core
)

from company_infra_construct import CompanyInfrastructure


class CoreInfrastructure(CompanyInfrastructure):
    """
    core shared infrastructure
    """

    # @property
    def redis_address(self) -> str:
        return self._redis_cache.attr_redis_endpoint_address

    # @property
    def redis_port(self) -> str:
        return self._redis_cache.attr_redis_endpoint_port

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        """ create our stack """
        super().__init__(scope, id, **kwargs)

        # redis cache cluster
        cache_subnet_group = elasticache.CfnSubnetGroup(
            self, 'subnet_group',
            description='elasticache subnet group',
            subnet_ids=['subnet-909a58bb']
        )

        self._redis_cache = elasticache.CfnCacheCluster(
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
            value=self._redis_cache.attr_redis_endpoint_address + ':' +
                  self._redis_cache.attr_redis_endpoint_port
        )