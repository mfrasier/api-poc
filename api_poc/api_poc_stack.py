from aws_cdk import (
    # aws_events as events,
    # aws_events_targets as targets,
    aws_apigateway as apigw,
    core
)

from external_api_construct import ExternalApi


class ApiPocStack(core.Stack):
    """
    Define our stack
    """
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        """ create our stack """
        super().__init__(scope, id, **kwargs)

        # external api construct
        external_api = ExternalApi(self, 'ExternalApi')

        # API Gateway frontend to simulator lambda
        external_gateway = apigw.LambdaRestApi(
            self, 'external_api',
            handler=external_api.handler,
            proxy=True
        )