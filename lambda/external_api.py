import json

"""
Simulate an external RESTful API service with client throttling
"""


def handler(event, context):
    print('request: {}'.format(json.dumps(event)))

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'Hello, CDK!  You have hit {}\n'.format(event['path'])
    }
