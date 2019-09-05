#!/usr/bin/env python3

from aws_cdk import (
    aws_events as events,
    aws_lambda as _lambda,
    aws_events_targets as targets,
    core,
)

from api_poc.api_poc_stack import ApiPocStack

app = core.App()
ApiPocStack(app, "api-poc-mfrasier", env={'region': 'us-east-1', 'account': '011955760856'})
app.synth()
