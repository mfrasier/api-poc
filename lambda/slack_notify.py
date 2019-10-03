'''
Follow these steps to configure the webhook in Slack:

  1. Navigate to https://<your-team-domain>.slack.com/services/new

  2. Search for and select "Incoming WebHooks".

  3. Choose the default channel where messages will be sent and click "Add Incoming WebHooks Integration".

  4. Copy the webhook URL from the setup instructions and use it in the next section.

To encrypt your secrets use the following steps:

  1. Create or use an existing KMS Key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html

  2. Click the "Enable Encryption Helpers" checkbox

  3. Paste <SLACK_CHANNEL> into the slackChannel environment variable

  Note: The Slack channel does not contain private info, so do NOT click encrypt

  4. Paste <SLACK_HOOK_URL> into the kmsEncryptedHookUrl environment variable and click encrypt

  Note: You must exclude the protocol from the URL (e.g. "hooks.slack.com/services/abc123").

  5. Give your function's role permission for the kms:Decrypt action.

     Example:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1443036478000",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": [
                "<your KMS key ARN>"
            ]
        }
    ]
}
'''

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

HOOK_URL = "https://" + boto3.client('ssm').get_parameter(
    Name=ENCRYPTED_HOOK_URL_KEY,
    WithDecryption=True
)['Parameter']['Value']
LOG.info(f"got key '{ENCRYPTED_HOOK_URL_KEY}' from ssm; value='{HOOK_URL}'")

SLACK_CHANNEL = boto3.client('ssm').get_parameter(
    Name=SLACK_CHANNEL_KEY,
)['Parameter']['Value']
LOG.info(f"got key '{SLACK_CHANNEL_KEY}' from ssm; value='{SLACK_CHANNEL}'")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    lambda entry point - triggered from SNS notification topic
    retrieve slack channel and decrypted webhook url from ssm parameter store
    send slack message
    :param event: SNS invocation; contains slack message in 'Message' key
    :param context: lambda context, unused
    """
    logger.info("Event: " + str(event))
    message = event['Records'][0]['Sns']['Message']
    logger.info("Message: " + str(message))

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
    # slack_message = {
    #     'channel': SLACK_CHANNEL,
        # 'text': message
    # }

    LOG.info(f"slack message: {slack_message}")
    req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to slack")
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
