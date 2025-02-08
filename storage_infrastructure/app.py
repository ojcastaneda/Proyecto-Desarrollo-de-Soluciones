#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infrastructure.infrastructure_stack import StorageStack


app = cdk.App()
StorageStack(app, "StorageStack")

app.synth()
