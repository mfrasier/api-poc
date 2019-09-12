#!/usr/bin/env python3

from aws_cdk import (
    core,
)

import redis

from core_stack import CoreStack
from api_poc.api_poc_stack import ApiPocStack
from api_consumer_stack import ApiConsumerStack

app = core.App()

CoreStack(app, "core-stack",
          env={'region': 'us-east-1', 'account': '011955760856', 'env': 'dev'})
ApiPocStack(app, "api-poc-mfrasier",
            env={'region': 'us-east-1', 'account': '011955760856', 'env': 'dev'})
ApiConsumerStack(app, 'api-consumer-mfrasier',
                 env={'region': 'us-east-1', 'account': '011955760856', 'env': 'dev'})

app.synth()
