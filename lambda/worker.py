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
    
TODO put failed work on dead letter queue
"""

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
NOTIFY_SNS_ARN = os.environ['THROTTLE_EVENTS_TOPIC']
REDIS_ADDRESS = os.environ['REDIS_ADDRESS']
REDIS_PORT = os.environ['REDIS_PORT']

r = redis.Redis(
    host=REDIS_ADDRESS,
    port=REDIS_PORT,
    decode_responses=True
)

sns = boto3.resource('sns')
notify_topic = sns.Topic(NOTIFY_SNS_ARN)


def handler(event, context):
    """
    main entry point
    event contains message from orchestrator
    """
    LOG.info('request: {}'.format(event))
    # perform_request(event)
    Worker(event)()


class Worker:
    def __init__(self, job):
        self.job = job
        self.api_key = self.job.get('api_id')
        self.operation = self.job.get('operation')
        self.url = self.job.get('api_url')
        self.resource = self.job.get('resource')

    def __call__(self, *args, **kwargs):
        self.perform_request()

    def perform_request(self) -> int:
        """
        coordinate http request and call specified operation
        :param event: lambda event object
        :return: status code of last operation
        """
        operation = self.job.get('operation')

        if operation is None:
            LOG.warning("exception handling job, unknown key 'operation'")
            return False

        response = self.perform_operation()
        LOG.info('response={}'.format(response.json()))
        status = response.status_code

        if 200 <= status < 300:
            LOG.warning('status {} returned for operation {}'.format(status, operation))
        else:
            # TODO requeue job
            self.open_circuit_breaker()

        if operation == 'NEW_SURVEYS':
            status = self.update_survey(response)
        elif operation == 'NEW_INTERVIEWS':
            status = self.update_interviews(response)
        elif operation == 'NEW_ATTACHMENTS':
            status = self.update_attachments(response)
        elif operation == 'HEALTH_CHECK':
            status = self.health_check(response)
        else:
            LOG.warning("exception handling job, unknown operation {}".format(operation))
            return False

        return status

    def perform_operation(self) -> dict:
        """
        perform http oeration request
        :param job: operation to perform
        :return: http response
        """
        operation = self.job.get('operation')
        url = self.url + self.resource
        LOG.info("querying '{}' for operation {}".format(url, operation))
        # TODO wrap in try block as it can fail
        response = requests.get(url)
        LOG.info('response: status_code={}, json={}'.format(response.status_code, response.json()))
        return response

    def update_survey(self, response: dict) -> int:
        """
        update survey data
        :param response: http response
        :return:
        """
        LOG.info('updating surveys')
        return 0

    def update_interviews(self, response: dict) -> int:
        """
        update interview data
        :param response: http response
        :return:
        """
        LOG.info('updating interviews')
        return 0

    def update_attachments(self, response: dict) -> int:
        """
        update attachment data
        :param response: http response
        :return:
        """
        LOG.info('updating attachments')
        return 0

    def health_check(self, response: dict) -> int:
        """
        perform health check of endpoint in response to work request
        :param response: http response
        :return:
        """
        status = response.status_code
        url = response.request.url
        LOG.info(f"health check response: {response}")

        if 200 <= status < 300 and url is not None:
            self.close_circuit_breaker()
        else:
            LOG.info('health checker taking no action for status={}, url={}'.format(status, url))

        return status

    def close_circuit_breaker(self) -> None:
        """
        close circuit breaker for api_key
        """
        # TODO check state first
        r.set(':'.join([self.api_key, 'state']), 'CLOSED')
        message = 'closed circuit breaker for api_key={}'.format(self.api_key)
        LOG.info(message)
        self.send_notification(message)

    def open_circuit_breaker(self) -> None:
        """
        open circuit breaker for api_key
        """
        # TODO check state first
        r.set(':'.join([self.api_key, 'state']), 'OPEN')
        message = 'opened circuit breaker for api_key={}'.format(self.api_key)
        LOG.info(message)
        self.send_notification(message)

    def send_notification(self, message: str) -> None:
        """
        send notification
        :param message:
        :return:
        """
        LOG.info('sending notification: message={}'.format(message))
        notify_topic.publish(
            Message = message
        )
