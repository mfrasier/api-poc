
from aws_cdk import (
    # aws_events as events,
    # aws_events_targets as targets,
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

        # external api construct
        external_api = ApiConsumer(self, 'ApiConsumer')
