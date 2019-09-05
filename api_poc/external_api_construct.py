from aws_cdk import (
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    core
)


class ExternalApi(core.Construct):
    """
    define our external API construct
    """
    @property
    def handler(self):
        return self.api_handler

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        table = dynamodb.Table(
            self, 'throttles',
            partition_key={'name': 'path', 'type': dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        # external API simulator lambda
        self.api_handler = _lambda.Function(
            self, "ExternalApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='external_api.handler',
            environment={
                'THROTTLE_TABLE_NAME': table.table_name
            },
            tracing=_lambda.Tracing.ACTIVE
        )

        table.grant_read_write_data(self.handler)
