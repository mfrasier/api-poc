from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_ec2 as ec2,
    core
)

from core_infra_construct import CoreInfrastructure
from company_infra_construct import CompanyInfrastructure
from cdk_watchful import Watchful


class ExternalApi(CompanyInfrastructure):
    """
    define our external API construct
    """
    # @property
    def api_gateway(self) -> apigw.RestApi:
        return self._api_gateway

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # external API simulator lambda
        api_handler = _lambda.Function(
            self, "ExternalApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            layers=[CompanyInfrastructure.python3_lib_layer],
            vpc=CompanyInfrastructure.vpc,
            vpc_subnets=CompanyInfrastructure.vpc_subnets,
            security_group=CompanyInfrastructure.security_group,
            tracing=_lambda.Tracing.ACTIVE
        )
        api_handler.add_environment('REDIS_ADDRESS', CoreInfrastructure.redis_address)
        api_handler.add_environment('REDIS_PORT', CoreInfrastructure.redis_port)

        # API Gateway frontend to simulator lambda
        self._api_gateway = apigw.LambdaRestApi(
            self, 'external_api',
            handler=api_handler,
            proxy=True
        )

        wf = Watchful(self, 'watch')
        # wf.watch_scope(self)
        wf.watch_lambda_function('api_function', api_handler)
