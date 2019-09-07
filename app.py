#!/usr/bin/env python3

from aws_cdk import (
    core,
)

import redis

from api_poc.api_poc_stack import ApiPocStack

app = core.App()
ApiPocStack(app, "api-poc-mfrasier", env={'region': 'us-east-1'})
app.synth()
