import json
import os
import logging
from time import gmtime, strftime

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
    
TODO add api_key to redis circuit breaker key construct
"""

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

NOTIFY_SNS_ARN = os.environ['THROTTLE_EVENTS_TOPIC']
JOB_QUEUE_URL = os.environ['JOB_QUEUE_URL']
REDIS_ADDRESS = os.environ['REDIS_ADDRESS']
REDIS_PORT = os.environ['REDIS_PORT']

r = redis.Redis(
    host=REDIS_ADDRESS,
    port=REDIS_PORT,
    decode_responses=True
)

sns = boto3.resource('sns')
notify_topic = sns.Topic(NOTIFY_SNS_ARN)
sqs = boto3.resource('sqs')
job_queue = sqs.Queue(JOB_QUEUE_URL)


def handler(event, context):
    """
    main entry point
    event contains message from orchestrator
    """
    LOG.info('request: {}'.format(event))
    Worker(event)()


class Worker:
    def __init__(self, event):
        self.CLOSED_STATE = 'CLOSED'
        self.OPEN_STATE = 'OPEN'
        self.job = event
        self.api_id = self.job.get('api_id')
        self.operation = self.job.get('operation')
        self.url = self.job.get('api_url')
        self.resource = self.job.get('resource')

    def __call__(self, *args, **kwargs):
        self.perform_request()

    def requeue_job(self, status:str) -> None:
        """
        requeue message to job queue for reprocessing
        :param status: http status code from failed call
        """
        job_queue.send_message(
            MessageBody=json.dumps(self.job),
            MessageAttributes={
                'requeued': {
                    'DataType': 'String',
                    'StringValue': 'true'
                },
                'status_code': {
                    'DataType': 'String',
                    'StringValue': str(status),
                },
            }
        )
        message = f'worker queued message to job queue for reprocessing; status code was {status}'
        LOG.info(message)
        self.send_notification(message)

    def perform_request(self) -> None:
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

        if status >= 400:
            LOG.warning('status {} returned for operation {}'.format(status, operation))
            # TODO requeue job
            # put message back on job queue
            self.open_circuit_breaker()
            self.requeue_job(status)

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
        key = ':'.join([self.api_id, 'state'])  # TODO make a class var - in conjunction with adding api_key
        key_state = r.get(key)
        LOG.info(f"circuit breaker state for key '{key}' is '{key_state}'")

        if key_state != self.CLOSED_STATE:
            r.set(key, 'CLOSED')
            message = 'worker closed circuit breaker for api_key={}'.format(self.api_id)
            LOG.info(message)
            self.send_notification(message)
        else:
            LOG.info(f'api_key {self.api_id} is already closed - no action taken')

    def open_circuit_breaker(self) -> None:
        """
        open circuit breaker for api_key
        """
        key = ':'.join([self.api_id, 'state'])
        key_state = r.get(key)
        LOG.info(f"circuit breaker state for key '{key}' is '{key_state}'")

        if key_state != self.OPEN_STATE:
            r.set(key, 'OPEN')
            message = 'worker opened circuit breaker for api_key={}'.format(self.api_id)
            LOG.info(message)
            self.send_notification(message)
        else:
            LOG.info(f'api_key {self.api_id} is already open - no action taken')

    def send_notification(self, message: str) -> None:
        """
        send notification
        :param message:
        :return:
        """
        LOG.info('sending notification: message={}'.format(message))
        time_str = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
        notify_topic.publish(
            Message=f"{time_str}: {message}"
        )
