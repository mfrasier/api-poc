#!/usr/bin/env python3

# TODO
# restrict API Gateway access to our VPC

from aws_cdk import (
    core,
)

from uber_stack import UberStack

app = core.App()

UberStack(app, 'api-uberstack-dev',
          tags={
              'Name': 'throttled api poc',
              'environment': 'dev'
          })

app.synth()
