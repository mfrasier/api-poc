import json
import os
import logging

import boto3
import redis
import requests

"""
job worker
invoked by orchestrator
inspects message to determine call to make
if message is health check
  call target system endpoint to check api_key quota status 
  if call succeeds
    mark target as CLOSED (circuit breaker)
else
  call target system resource api
  if call succeeds
    perform business logic
  else
    mark path as OPEN (circuit breaker)
"""

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT'],
    decode_responses=True
)

notify_sns_arn = os.environ['THROTTLE_EVENTS_TOPIC']

sns = boto3.resource('sns')
notify_topic = sns.Topic(notify_sns_arn)


def handler(event, context):
    """
    main entry point
    event contains message from orchestrator
    """
    LOG.info('request: {}'.format(json.dumps(event)))

    try:
        if event['operation'] == 'NEW_SURVEYS':
            update_survey(event)
    except KeyError as e:
        LOG.warning("exception handling job, unknown key 'operation'")
        LOG.info('job: '.format(event))


def update_survey(job: dict) -> None:
    url = job['api_url'] + job['resource']
    LOG.info("querying '{}' for new surveys".format(url))
    response = requests.get(url)
    LOG.info('response: status={}, json={}'.format(response.status_code, response.json()))

    if response.status_code == 429:
        message = 'exceeded quota at {}'.format(url)
        LOG.info(message)
        open_circuit_breaker(url)
        send_notification(message)


def send_notification(message):
    LOG.info('sending notification: message={}'.format(message))
    notify_topic.publish(
        Message = message
    )


def open_circuit_breaker(url: str):
    LOG.info('opening circuit breaker for url={}'.format(url))
