from aws_cdk import (
    core
)

from core_infra_construct import CoreInfrastructure


class CoreStack(core.Stack):
    """
    core stack
    """
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        """ create our stack """
        super().__init__(scope, id, **kwargs)

        # api consumer construct
        CoreInfrastructure(self, 'CoreInfrastructure')