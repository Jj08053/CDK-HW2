import aws_cdk as cdk
import os.path

from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_s3_assets as s3_assets,
    aws_rds as rds, 
    
)

from constructs import Construct

dirname = os.path.dirname(__file__)

class CdkLabWebServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cdk_lab_vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define an IAM role for an EC2 instance that allows it to use AWS Systems Manager (SSM)
        self.instance_ssm_role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        self.instance_ssm_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        
        # Web Servers Security Group
        self.web_servers_security_group = ec2.SecurityGroup(self,"ec2_SG",vpc=cdk_lab_vpc,description="Security_group_for_web_servers")
        self.web_servers_security_group.add_ingress_rule(ec2.Peer.any_ipv4(),
                                                        ec2.Port.tcp(80), 
                                                        "Open_port_80_from_anywhere")
        
        # Create one EC2 instance at public subnet of us-east-1a    
        self.cdk_lab_web_instance_1 = ec2.Instance(self,
                                            "cdk_lab_web_instance_1",
                                            vpc=cdk_lab_vpc,
                                            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            vpc_subnets=ec2.SubnetSelection(availability_zones=["us-east-1a"],
                                                                            subnet_type=ec2.SubnetType.PUBLIC),
                                            security_group=self.web_servers_security_group,
                                            role=self.instance_ssm_role
                                            )
        
        # Create one EC2 instance at public subnet of us-east-1b
        self.cdk_lab_web_instance_2 = ec2.Instance(self,
                                            "cdk_lab_web_instance_2",
                                            vpc=cdk_lab_vpc,
                                            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            vpc_subnets=ec2.SubnetSelection(availability_zones=["us-east-1b"],
                                                                            subnet_type=ec2.SubnetType.PUBLIC),
                                            security_group=self.web_servers_security_group,
                                            role=self.instance_ssm_role
                                            )
      
        # Script in S3 as Asset
        self.webinitscriptasset = s3_assets.Asset(self, "WebServerConfigAsset", path=os.path.join(dirname, "configure.sh"))
        self.asset_path_1 = self.cdk_lab_web_instance_1.user_data.add_s3_download_command(
            bucket=self.webinitscriptasset.bucket,
            bucket_key=self.webinitscriptasset.s3_object_key
        )
        self.asset_path_2 = self.cdk_lab_web_instance_2.user_data.add_s3_download_command(
            bucket=self.webinitscriptasset.bucket,
            bucket_key=self.webinitscriptasset.s3_object_key
        )

        # Userdata executes script from S3
        self.cdk_lab_web_instance_1.user_data.add_execute_file_command(
            file_path=self.asset_path_1
        )
        self.cdk_lab_web_instance_2.user_data.add_execute_file_command(
            file_path=self.asset_path_2
        )
        
        self.webinitscriptasset.grant_read(self.instance_ssm_role)
        
        # RDS Security Group
        self.rds_security_group = ec2.SecurityGroup(self,"RDS_SG",vpc=cdk_lab_vpc,description="RDS_security_group")
        self.rds_security_group.add_ingress_rule(self.web_servers_security_group,
                                                ec2.Port.tcp(3306), 
                                                "Open_port_3306_to_only_EC2s_security_group")
        
        # Create subnet group for RDS instance
        self.rds_subnet_group = rds.SubnetGroup(self, "PrivateSubnetGroup",
                                        description="Contains_all_private_subnets",
                                        vpc=cdk_lab_vpc,
                                        removal_policy=cdk.RemovalPolicy.DESTROY,
                                        vpc_subnets=ec2.SubnetSelection(
                                            availability_zones=["us-east-1a", "us-east-1b"],
                                            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                                        )
                                    )
        
        # Create RDS instance
        self.rds_instance = rds.DatabaseInstance(self, "MySQL_instance",
                                    engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0),
                                    instance_type=ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
                                    allocated_storage= 20,
                                    # Generate the secret with admin username `admin` and random password
                                    # The database password will be auto generated and stored in the secrets manager
                                    credentials=rds.Credentials.from_generated_secret("DB_admin"),
                                    security_groups=[self.rds_security_group],
                                    subnet_group=self.rds_subnet_group,
                                    port=3306,
                                    vpc=cdk_lab_vpc,
                                    vpc_subnets=ec2.SubnetSelection(
                                        availability_zones=["us-east-1a", "us-east-1b"],
                                        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                                    ),
                                    removal_policy=cdk.RemovalPolicy.DESTROY,
                                    deletion_protection= False,
                            )
        
