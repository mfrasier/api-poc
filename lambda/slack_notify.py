
import boto3
import json
import logging
import os

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

ENCRYPTED_HOOK_URL_KEY = os.environ['encryptedHookUrlKey']
SLACK_CHANNEL_KEY = os.environ['slackChannelKey']
NOTIFY_SLACK = True if os.getenv('notifySlack', 'FALSE').upper() == 'TRUE' else False

if NOTIFY_SLACK:
    HOOK_URL = "https://" + boto3.client('ssm').get_parameter(
        Name=ENCRYPTED_HOOK_URL_KEY,
        WithDecryption=True
    )['Parameter']['Value']
    LOG.info(f"got key '{ENCRYPTED_HOOK_URL_KEY}' from ssm; value='{HOOK_URL}'")

    SLACK_CHANNEL = boto3.client('ssm').get_parameter(
        Name=SLACK_CHANNEL_KEY,
    )['Parameter']['Value']
    LOG.info(f"got key '{SLACK_CHANNEL_KEY}' from ssm; value='{SLACK_CHANNEL}'")
else:
    LOG.info(f"slack_notification is disabled via config. NOTIFY_SLACK={NOTIFY_SLACK}")


def lambda_handler(event, context):
    """
    lambda entry point - triggered from SNS notification topic
    retrieve slack channel and decrypted webhook url from ssm parameter store
    send slack message
    :param event: SNS invocation; contains slack message in 'Message' key
    :param context: lambda context, unused
    """
    LOG.info("Event: " + str(event))
    message = event['Records'][0]['Sns']['Message']
    LOG.info("Message: " + str(message))

    if NOTIFY_SLACK:
        title = 'Notification'
        color = 'good'
        if 'open' in message.lower():
            title = 'Opened Circuit Breaker'
            color = 'warning'
        elif 'close' in message.lower():
            title = 'Closed Circuit Breaker'
            color = 'good'
        elif 'orchestrator' in message.lower():
            title = 'Orchestrator'
            color = 'good'

        slack_message = {
            # "text": message,
            "attachments": [
                {
                    "fallback": message,
                    # "pretext": "Message Processor Notification",
                    "color": color,
                    "fields": [
                        {
                            "title": title,
                            "value": message,
                            "short": False
                        }
                    ]
                }
            ]
        }

        LOG.info(f"slack message: {slack_message}")
        req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
        try:
            response = urlopen(req)
            response.read()
            LOG.info("Message posted to slack")
        except HTTPError as e:
            LOG.error("Request failed: %d %s", e.code, e.reason)
        except URLError as e:
            LOG.error("Server connection failed: %s", e.reason)
    else:
        LOG.info(f'notifySlack is {NOTIFY_SLACK}; not sending notification')
