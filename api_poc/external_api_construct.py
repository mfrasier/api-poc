from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    core
)


class ExternalApi(core.Construct):
    """
    define our external API construct
    """

    @property
    def gateway(self):
        return self.gateway

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # external API simulator lambda
        self.lambda_api = _lambda.Function(
            self, "ExternalApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            tracing=_lambda.Tracing.ACTIVE
        )

        # API Gateway frontend to simulator lambda
        self.gateway = apigw.LambdaRestApi(
            self, 'external_api',
            handler=self.lambda_api
        )