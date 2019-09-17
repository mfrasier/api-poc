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

sqs = boto3.resource('sqs')
work_queue_url = os.environ['JOB_QUEUE_URL']
work_dlq_url = os.environ['JOB_DLQ_URL']
LOG.info('queue_url={}'.format(work_queue_url))
work_queue = sqs.Queue(work_queue_url)
work_dlq = sqs.Queue(work_dlq_url)

_lambda = boto3.client('lambda')
worker_arn = os.environ['WORKER_FUNCTION_ARN']


def handler(event, context):
    """
    main entry point
    event contains dict from cloudwatch rule (content ignored - just triggers)
    """
    throttle_state = hydrate_state()
    # check throttle state here
    process_messages(work_queue)


def process_messages(queue: 'Queue') -> None:
    LOG.info('getting messages from work queue {}'.format(work_queue_url))
    messages = queue.receive_messages(
        AttributeNames=['All'],
        MaxNumberOfMessages=10,
        VisibilityTimeout=10,
    )
    LOG.info('received {} messages from work queue '.format(len(messages), queue))

    for message in messages:
        LOG.info('message id: {}'.format(message.message_id))
        LOG.info('message body: {}'.format(message.body))

        # process message
        LOG.info('invoking lambda function {}'.format(worker_arn))
        response = _lambda.invoke(
            FunctionName=worker_arn,
            InvocationType='Event',
            Payload=message.body
        )
        LOG.info('lambda invocation returned {}'.format(response))

        # delete() if all went well


def hydrate_state() -> dict:
    state = []
    LOG.info('rehydrating current throttle state')
    keys = r.keys('survey:*')

    # could use lock or pipeline here if it becomes necessary
    for key in keys:
        state.append({'name': key, 'value': r.get(key), 'ttl': r.ttl(key)})

    LOG.info('hydrated state: {}'.format(state))
    return state
