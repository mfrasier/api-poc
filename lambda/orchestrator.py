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


def handler(event, context):
    """
    main entry point
    event contains dict from api gateway request
    """
    LOG.info('request: {}'.format(json.dumps(event)))
    queue_url = os.environ['SQS_URL']
    LOG.info('queue_url={}'.format(queue_url))

    throttle_state = hydrate_state()
    sqs = boto3.resource('sqs')
    work_queue = sqs.Queue(queue_url)
    process_messages(work_queue)


def process_messages(queue: 'Queue') -> None:
    messages = queue.receive_messages(MaxNumberOfMessages=10)
    LOG.info(messages)


def hydrate_state() -> dict:
    state = {}
    keys = r.keys('survey:*')

    # could use lock or pipeline here if it becomes necessary
    for key in keys:
        state['key'] = {'name': key, 'value': r.get(key), 'ttl': r.ttl(key)}

    return state