
from aws_cdk import (
    core
)

from api_consumer_construct import ApiConsumer


class ApiConsumerStack(core.Stack):
    """
    api consumer stack
    """
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        """ create our stack """
        super().__init__(scope, id, **kwargs)

        # api consumer construct
        ApiConsumer(self, 'ApiConsumer')
