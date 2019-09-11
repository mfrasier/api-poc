from aws_cdk import (
    core
)

from external_api_construct import ExternalApi

# TODO add vpc for dedicated use for this project


class ApiPocStack(core.Stack):
    """
    external api server stack
    """
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        """ create our stack """
        super().__init__(scope, id, **kwargs)

        # external api construct
        external_api = ExternalApi(self, 'ExternalApi')
