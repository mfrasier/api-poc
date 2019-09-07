import json
import os
from datetime import datetime
import logging

import redis
import boto3

"""
Simulate an external RESTful API service with client throttling
"""
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
ddb = boto3.resource('dynamodb')
table = ddb.Table(os.environ['THROTTLE_TABLE_NAME'])

# r = redis.Redis(
#     host=os.environ('REDIS_ADDRESS'),
#     port=os.environ('REDIS_PORT')
# )


def handler(event, context):
    """
    main entry point
    event contains dict from api gateway request
    """
    LOG.info('request: {}'.format(json.dumps(event)))
    LOG.info('throttle tracking table={}'.format(table))

    # r.set('foo', 'bar')
    # value = r.value('foo')
    # print('value of foo={}'.format(value))

    table.update_item(
        Key={'path': event['path']},
        UpdateExpression='SET hits = if_not_exists(hits, :zero) + :inc, last_hit = :t',
        ExpressionAttributeValues={':zero': 0, ':inc': 1, ':t': str(datetime.utcnow())}
    )

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'Hello, CDK!  You have hit {}\n'.format(event['path'])
    }
