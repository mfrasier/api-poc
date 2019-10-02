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

api_url = os.environ['API_HOST_URL']
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
    """
    create and send message(s) to work queue
    :param function_id: id of message source - lambda arn
    """
    send_survey_work_message(function_id)
    send_interview_work_message(function_id)
    send_attachment_work_message(function_id)
    send_survey_work_message(function_id)
    send_interview_work_message(function_id)
    send_attachment_work_message(function_id)


def send_message(message: dict) -> None:
    """ send message to queue """
    work_queue.send_message(
        MessageBody=json.dumps(message)
    )
    LOG.info('sent message to SQS: {}'.format(message))


def send_survey_work_message(source_id: str) -> None:
    """create and send a survey message to work queue"""
    send_message({
        'operation': 'NEW_SURVEYS',
        'api_id': 'ODG_SURVEYS',
        'api_url': api_url,
        'resource': 'survey',
        'source_id': source_id,
    })


def send_interview_work_message(source_id: str) -> None:
    """create and send a interview message to work queue"""
    send_message({
        'operation': 'NEW_INTERVIEWS',
        'api_id': 'ODG_SURVEYS',
        'api_url': api_url,
        'resource': 'survey/1/interview',
        'source_id': source_id,
    })


def send_attachment_work_message(source_id: str) -> None:
    """create and send a attachment message to work queue"""
    send_message({
        'operation': 'NEW_ATTACHMENTS',
        'api_id': 'ODG_SURVEYS',
        'api_url': api_url,
        'resource': 'survey/1/interview/1/attachment',
        'source_id': source_id,
    })


def send_health_check_message(source_id: str) -> None:
    """create and send a health check message to work queue"""
    send_message({
        'operation': 'HEALTH_CHECK',
        'api_id': 'ODG_SURVEYS',
        'api_url': api_url,
        'resource': 'health',
        'source_id': source_id,
    })