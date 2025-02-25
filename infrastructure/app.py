"""CDK application to deploy the infrastructure."""

import os

import aws_cdk as cdk

from infrastructure.storage import StorageStack
from infrastructure.server import ServerStack

env = {
    "account": os.getenv("CDK_DEFAULT_ACCOUNT"),
    "region": os.getenv("CDK_DEFAULT_REGION"),
}

app = cdk.App()
storage = StorageStack(app, "StorageStack", env=env)
ServerStack(app, "ServerStack", env=env, bucket=storage.bucket)

app.synth()
