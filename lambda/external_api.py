import json
import os
from datetime import datetime

import boto3

"""
Simulate an external RESTful API service with client throttling
"""

ddb = boto3.resource('dynamodb')
table = ddb.Table(os.environ['THROTTLE_TABLE_NAME'])


def handler(event, context):
    """
    main entry point
    event contains dict from api gateway request
    """
    print('request: {}'.format(json.dumps(event)))
    print('throttle tracking table={}'.format(table))

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
