import json
import os
import logging

import boto3
import redis

"""
job orchestrator
invoked on schedule by cloudwatch event
read messages from job_queue, invoke task worker lambdas
"""

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT'],
    decode_responses=True
)

queue_arn = os.environ['SQS_ARN']
sqs = boto3.client('sqs')


def handler(event, context):
    """
    main entry point
    event contains dict from api gateway request
    """
    LOG.info('request: {}'.format(json.dumps(event)))
    LOG.info('queue_arn={}'.format(queue_arn))


def process_messages(queue_arn: str) -> None:
    pass


def hydrate_state() -> None:
