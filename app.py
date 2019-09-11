#!/usr/bin/env python3

from aws_cdk import (
    core,
)

import redis

from api_poc.api_poc_stack import ApiPocStack
from api_consumer_stack import ApiConsumerStack

app = core.App()
ApiPocStack(app, "api-poc-mfrasier", env={'region': 'us-east-1', 'account': '011955760856'})
ApiConsumerStack(app, 'api-consumer-mfrasier', env={'region': 'us-east-1', 'account': '011955760856'})
app.synth()
