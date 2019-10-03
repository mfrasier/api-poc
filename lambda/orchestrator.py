import json
import os
from time import sleep
from datetime import date
from time import gmtime, strftime
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

NOTIFY_SNS_ARN = os.environ['THROTTLE_EVENTS_TOPIC']
SLEEP_SECONDS = 1
MY_FUNCTION_NAME = None
API_URL = os.environ['API_HOST_URL']
WORK_QUEUE_URL = os.environ['JOB_QUEUE_URL']
WORK_DLQ_URL = os.environ['JOB_DLQ_URL']

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT'],
    decode_responses=True
)

sns = boto3.resource('sns')
notify_topic = sns.Topic(NOTIFY_SNS_ARN)
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
    total_messages = 0
    total_requeued = 0

    time_str = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    notify_topic.publish(
        Message=f"{time_str}: orchestrator started",
    )

    while True:
        hydrate_state()
        api_state = state.get(f'{api_id}:state', 'CLOSED')

        if api_state == 'OPEN':
            LOG.info(f'api state for id {api_id} is {api_state}, invoking health check')
            health_check()
        else:
            LOG.info(f'api state for id {api_id} is {api_state}, invoking message processor')

            messages_processed, requeued_messages = process_messages(work_queue)
            total_messages = total_messages + messages_processed
            total_requeued = total_requeued + requeued_messages

            if messages_processed == 0:
                LOG.info(f'cleared work queue - finished run.  Processed {total_messages} messages, '
                         f'of which {total_requeued} had been requeued')
                time_str = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
                notify_topic.publish(
                    Message=f"{time_str}: orchestrator exiting.\nProcessed {total_messages} messages; "
                    f"{total_requeued} had been requeued.",
                )
                return
            else:
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
        MessageAttributeNames=['All'],
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
    requeued_messages = 0
    LOG.info('getting messages from work queue {}'.format(WORK_QUEUE_URL))

    messages = _receive_messages(queue)
    LOG.info('received {} messages from work queue '.format(len(messages), queue))

    if len(messages) == 0:
        return messages_processed, requeued_messages

    for message in messages:
        LOG.info('message id: {}'.format(message.message_id))
        LOG.info(f"message: {message}")
        if message.message_attributes is not None:
            if 'requeued' in message.message_attributes:
                requeued_messages = requeued_messages + 1

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

    return messages_processed,requeued_messages


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
