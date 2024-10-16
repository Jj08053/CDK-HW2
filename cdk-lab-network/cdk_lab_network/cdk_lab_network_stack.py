from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam
)
from constructs import Construct

class CdkLabNetworkStack(Stack):
    
    @property
    def vpc(self):
        return self.cdk_lab_vpc

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC. CDK by default creates and attaches internet gateway for VPC
        self.cdk_lab_vpc = ec2.Vpc(self, "cdk_lab_vpc", 
                                    ip_addresses = ec2.IpAddresses.cidr("10.0.0.0/16"), 
                                    subnet_configuration=[
                                        ec2.SubnetConfiguration(
                                            name='Public',
                                            subnet_type=ec2.SubnetType.PUBLIC,
                                            cidr_mask=20
                                        ), 
                                        ec2.SubnetConfiguration(
                                            name='Private',   
                                            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,            
                                            cidr_mask=20
                                        )
                                    ],
                                    availability_zones = ["us-east-1a", "us-east-1b"])
