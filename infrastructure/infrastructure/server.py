"""Server module."""

import os
from pathlib import Path

import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_iam as iam
from constructs import Construct


UBUNTU_24_04_AMI_ID = "ami-04b4f1a9cf54c11d0"
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


class ServerStack(cdk.Stack):
    """Stack including the resources that need to be provisioned in order to
    host an MLflow server."""

    def __init__(
        self, scope: Construct, construct_id: str, bucket: s3.Bucket, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        default_vpc = ec2.Vpc.from_lookup(
            self,
            "VPC",
            is_default=True,
        )
        security_group = ec2.SecurityGroup(
            self,
            "MLflowSecurityGroup",
            vpc=default_vpc,
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(5000),
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
        )
        role = iam.Role(
            self,
            "MLflowRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:ListBucket",
                    "s3:HeadObject",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                ],
                resources=[
                    bucket.bucket_arn + "/*",
                    bucket.bucket_arn,
                ],
            )
        )
        instance = ec2.Instance(
            self,
            "MLflowInstance",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2,
                ec2.InstanceSize.MICRO,
            ),
            machine_image=ec2.MachineImage.generic_linux(
                {
                    os.getenv("CDK_DEFAULT_REGION"): UBUNTU_24_04_AMI_ID,
                }
            ),
            vpc=default_vpc,
            security_group=security_group,
            role=role,
            key_pair=ec2.KeyPair(
                self,
                "MLflowKeyPair",
                key_pair_name="mlflow-key-pair",
                type=ec2.KeyPairType.RSA,
            ),
        )
        with open(SCRIPTS_DIR / "init_script.sh", encoding="utf-8") as file:
            init_script = file.read()
        instance.add_user_data(init_script)
