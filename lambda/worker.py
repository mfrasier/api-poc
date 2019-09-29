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
    LOG.info('request: {}'.format(event))
    perform_request(event)


def perform_request(event: dict) -> int:
    """
    coordinate http request and call specified operation
    :param event: lambda event object
    :return: status code of last operation
    """
    operation = event.get('operation')

    if operation is None:
        LOG.warning("exception handling job, unknown key 'operation'")
        return False

    response = perform_operation(event)
    LOG.info('response={}'.format(response.json()))
    status = response.status_code
    api_key = event.get('api_id')

    if 200 <= status < 300:
        LOG.warning('status {} returned for operation {}'.format(status, operation))
    else:
        # TODO requeue job
        open_circuit_breaker(api_key)

    if operation == 'NEW_SURVEYS':
        status = update_survey(response)
    elif operation == 'NEW_INTERVIEWS':
        status = update_interviews(response)
    elif operation == 'NEW_ATTACHMENTS':
        status = update_attachments(response)
    elif operation == 'HEALTH_CHECK':
        status = health_check(response, api_key)
    else:
        LOG.warning("exception handling job, unknown operation {}".format(operation))
        return False

    return status


def perform_operation(job: dict) -> dict:
    """
    perform http oeration request
    :param job: operation to perform
    :return: http response
    """
    operation = job.get('operation')
    url = job['api_url'] + job['resource']
    LOG.info("querying '{}' for operation {}".format(url, operation))
    # TODO wrap in try block as it can fail
    response = requests.get(url)
    LOG.info('response: status_code={}, json={}'.format(response.status_code, response.json()))
    return response


def update_survey(response: dict) -> int:
    """
    update survey data
    :param response: http response
    :return:
    """
    LOG.info('updating surveys')
    return 0


def update_interviews(response: dict) -> int:
    """
    update interview data
    :param response: http response
    :return:
    """
    LOG.info('updating interviews')
    return 0


def update_attachments(response: dict) -> int:
    """
    update attachment data
    :param response: http response
    :return:
    """
    LOG.info('updating attachments')
    return 0


def health_check(response: dict, api_key: str) -> int:
    """
    perform health check of endpoint in response to work request
    :param response: http response
    :param api_key: api_key of endpoint
    :return:
    """
    status = response.status_code
    url = response.request.url
    LOG.info(f"health check response: {response}")

    if 200 <= status < 300 and url is not None:
        # TODO check state first?
        close_circuit_breaker(api_key)
    else:
        LOG.info('health checker taking no action for status={}, url={}'.format(status, url))

    return status


def close_circuit_breaker(api_key: str):
    """
    close circuit breaker for api_key
    :param api_key: api key from event
    :return:
    """
    r.set(':'.join([api_key, 'state']), 'CLOSED')
    message = 'closed circuit breaker for api_key={}'.format(api_key)
    LOG.info(message)
    send_notification(message)


def open_circuit_breaker(api_key: str):
    """
    open circuit breaker for api_key
    :param api_key: api key from event
    :return:
    """
    r.set(':'.join([api_key, 'state']), 'OPEN')
    message = 'opened circuit breaker for api_key={}'.format(api_key)
    LOG.info(message)
    send_notification(message)


def send_notification(message):
    """
    send notification
    :param message:
    :return:
    """
    LOG.info('sending notification: message={}'.format(message))
    notify_topic.publish(
        Message = message
    )
