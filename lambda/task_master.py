import json
import os
import logging

import boto3
import redis

"""
task master
invoked on schedule by cloudwatch event
puts messages into work queue to be performed
"""

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT'],
    decode_responses=True
)

host_url = os.environ['API_HOST_URL']
sqs = boto3.resource('sqs')
queue_url = os.environ['SQS_URL']
LOG.info('queue_url={}'.format(queue_url))
work_queue = sqs.Queue(queue_url)


def handler(event, context):
    """
    main entry point
    event contains dict from cloudwatch rule (content ignored - just triggers)
    """
    LOG.info('request: {}'.format(json.dumps(event)))
    function_id = '{}:{}'.format(context.function_name, context.function_version)
    create_work(function_id)


def create_work(function_id: str)-> None:
    msg_body = {
        'operation': 'NEW_SURVEYS',
        'api_id': 'ODG_SURVEYS',
        'host_url': host_url,
        'resource': 'survey',
        'source': function_id,
    }

    work_queue.send_message(
        MessageBody=json.dumps(msg_body)
    )
    LOG.info('sent work message to SQS: {}'.format(msg_body))