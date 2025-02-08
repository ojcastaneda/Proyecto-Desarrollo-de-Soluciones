"""Infrastructure stack module."""
import aws_cdk as cdk
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_iam as iam
from constructs import Construct


class StorageStack(cdk.Stack):
    """Stack including the resources that need to be provisioned in order to
    work with DVC using s3 as storage."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        bucket = s3.Bucket(
            self,
            "DVCStorageBucket",
            bucket_name="maia-202511-g5-dvc-storage-bucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        user = iam.User(
            self,
            "DVCUser",
            user_name="dvc-user",
        )
        user.add_to_policy(
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
