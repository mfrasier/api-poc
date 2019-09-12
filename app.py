#!/usr/bin/env python3

from aws_cdk import (
    core,
)

from uber_stack import UberStack

app = core.App()

UberStack(app, 'api-uberstack-mfrasier',
                 env={'region': 'us-east-1', 'account': '011955760856', 'env': 'dev'})

app.synth()
