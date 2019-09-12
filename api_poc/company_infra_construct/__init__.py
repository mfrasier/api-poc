from aws_cdk import (
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    core
)


class CompanyInfrastructure(core.Construct):
    """
    parent class for constructs in our company
    provides common attributes and functions
    """

    # @property
    def python3_lib_layer(self) -> _lambda.LayerVersion:
        return self._python3_lib_layer

    # @property
    def security_group(self) -> ec2.SecurityGroup:
        return self._security_group

    # @property
    def vpc(self) -> ec2.Vpc:
        return self._vpc

    # @property
    def vpc_subnets(self) -> ec2.SubnetSelection:
        return self._vpc_subnets


    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self._vpc = ec2.Vpc.from_lookup(
            self, 'my_vpc',
            vpc_name='MyVPC1'
        )

        self._vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE)

        self._security_group = ec2.SecurityGroup.from_security_group_id(
            self, 'default-sg',
            security_group_id='sg-9d857bf9'
        )

        # TODO someday, create the layer from local zip file
        self._python3_lib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, 'python3-lib-layer',
            layer_version_arn='arn:aws:lambda:us-east-1:011955760856:layer:python3-lib-layer:1'
        )


__all__ = ["CompanyInfrastructure"]