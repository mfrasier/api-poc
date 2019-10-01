import json
import os
from time import sleep
from datetime import date
import logging

import boto3
import redis

"""
job orchestrator for api ODG_SURVEYS
invoked on schedule by cloudwatch event
read messages from job_queue, invoke task worker lambdas

TODO: manage API stats
"""

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT'],
    decode_responses=True
)

SLEEP_SECONDS = 5
MY_FUNCTION_NAME = None
API_URL = os.environ['API_HOST_URL']
WORK_QUEUE_URL = os.environ['JOB_QUEUE_URL']
WORK_DLQ_URL = os.environ['JOB_DLQ_URL']

sqs = boto3.resource('sqs')
work_queue = sqs.Queue(WORK_QUEUE_URL)
work_dlq = sqs.Queue(WORK_DLQ_URL)

_lambda = boto3.client('lambda')
worker_arn = os.environ['WORKER_FUNCTION_ARN']

api_id = 'ODG_SURVEYS'
stats_hash = 'stats:invoke'
state = {}
batch_num = 0


def handler(event, context):
    """
    main entry point
    event contains dict from cloudwatch rule (content ignored - just triggers)
    """
    global MY_FUNCTION_NAME, batch_num
    LOG.info('starting orchestrator...')
    MY_FUNCTION_NAME = context.function_name
    while True:
        hydrate_state()
        api_state = state.get(f'{api_id}:state', 'CLOSED')

        if api_state == 'OPEN':
            LOG.info(f'api state for id {api_id} is {api_state}, invoking health check')
            health_check()
        else:
            LOG.info(f'api state for id {api_id} is {api_state}, invoking message processor')
            if process_messages(work_queue) == 0:
                LOG.info('cleared work queue - finished run.')
                return
            else:
                # TODO use message tracker to update data store
                batch_num = batch_num + 1
                LOG.info(f'completed batch {batch_num} of work messages')


def _receive_messages(queue: 'boto3.SQS.Queue', count: int = 10) -> list:
    """
    receive messages from queue
    :param queue: queue to receive messages from
    :param count: max number of msgs to receive
    :return: list of Message
    """
    return queue.receive_messages(
        AttributeNames=['All'],
        MaxNumberOfMessages=count,
        VisibilityTimeout=10,
    )


def job_attribute(message: 'Message', attribute_name: str) -> 'Any':
    """
    inspect message body for requested attribute
    :param message: Message to inspect
    :param attribute_name: requested attribute name
    :return: attribute value or None
    """
    return message.body.get(attribute_name)


def process_messages(queue: 'boto3.SQS.Queue') -> int:
    """
    Process messages from queue by invoking worker function for each message.
    :param queue: queue to receive messages from
    :return: count of messages processed
    """
    messages_processed = 0
    LOG.info('getting messages from work queue {}'.format(WORK_QUEUE_URL))

    messages = _receive_messages(queue)
    LOG.info('received {} messages from work queue '.format(len(messages), queue))

    if len(messages) == 0:
        return 0

    for message in messages:
        LOG.info('message id: {}'.format(message.message_id))

        # process message
        LOG.info('invoking lambda function {} with message: {}'.format(worker_arn, message.body))
        response = _lambda.invoke(
            FunctionName=worker_arn,
            InvocationType='Event', # async
            Payload=message.body
        )

        # populate stats tracker
        stats_key = ':'.join([date.strftime(date.today(), "%Y-%m-%d"), api_id])
        print(f'incrementing stats counter for key {stats_key}')
        r.hincrby('stats:invoke', stats_key)

        LOG.info('lambda invocation returned {}'.format(response))
        message.delete() # if all went well
        messages_processed = messages_processed + 1

    return messages_processed


def health_check():
    """api circuit breaker is not closed, send health check message"""
    message = {
        'operation': 'HEALTH_CHECK',
        'api_id': 'ODG_SURVEYS',
        'api_url': API_URL,
        'resource': 'health',
        'source_id': MY_FUNCTION_NAME,
    }
    _lambda.invoke(
        FunctionName=worker_arn,
        InvocationType='Event',  # async
        Payload=json.dumps(message)
    )
    LOG.info(f'invoked worker with health check message; sleeping {SLEEP_SECONDS} seconds')
    sleep(SLEEP_SECONDS)
    hydrate_state()


def hydrate_state() -> None:
    state.clear()
    LOG.info('hydrating current throttle states')
    keys = r.keys('*:state')

    for key in keys:
        state[key] = r.get(key)

    LOG.info('hydrated state: {}'.format(state))
