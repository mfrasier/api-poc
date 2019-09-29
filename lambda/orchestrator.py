import json
import os
from time import sleep
import logging

import boto3
import redis

"""
job orchestrator
invoked on schedule by cloudwatch event
read messages from job_queue, invoke task worker lambdas
TODO: manage API state - set state for any api_id encountered and not in hydrated state.
TODO: check state periodically in case workers have updated it, (update?)
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
            LOG.info(f'api state is {api_state}, invoking health check')
            health_check()
        else:
            LOG.info(f'api state is {api_state}, invoking message processor')
            if process_messages(work_queue) == 0:
                LOG.info('cleared work queue - finished run.')
                return
            else:
                # TODO use message tracker to update data store
                batch_num = batch_num + 1
                LOG.info(f'completed batch {batch_num} of work messages')


def _receive_messages(queue: 'boto3.SQS.Queue', count: int = 10) -> list:
    return queue.receive_messages(
        AttributeNames=['All'],
        MaxNumberOfMessages=count,
        VisibilityTimeout=10,
    )


def process_messages(queue: 'boto3.SQS.Queue') -> int:
    LOG.info('getting messages from work queue {}'.format(WORK_QUEUE_URL))

    # TODO check local copy of endpoint state to see whether to send health_check or get messages from queue
    #
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

        # TODO populate message tracker

        LOG.info('lambda invocation returned {}'.format(response))
        message.delete() # if all went well


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
