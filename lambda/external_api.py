import json
import os
import logging
import re
from collections import namedtuple

import redis
import boto3

"""
Simulate an external RESTful API service with client throttling
"""
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
ddb = boto3.resource('dynamodb')
table = ddb.Table(os.environ['THROTTLE_TABLE_NAME'])

Response = namedtuple('Response', ['status_code', 'data', 'key', 'quota'])

# throttle thresholds
thresholds = {
    'global': {
        'interval': 60 * 60,
    },
    'survey': {
        'count': 50
    },
    'survey:interview': {
        'count': 25
    },
    'survey:interview:attachment': {
        'count': 10
    }
}


# match incoming path to ascertain resource
# pattern=re.compile(r'^/(survey)(?:/)?(?:/\d*)?/(interview)(?:/)?(?:/\d*)/(attachment)(?:/)?(?:\d*)?')
pattern = r'/([a-zA-Z]+)'

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT']
)

LOG.info(r)

def handler(event, context):
    """
    main entry point
    event contains dict from api gateway request
    """
    LOG.info('request: {}'.format(json.dumps(event)))
    LOG.info('throttle tracking table={}'.format(table))
    LOG.info('redis address: {}'.format(os.environ['REDIS_ADDRESS']))

    api_key = 'none'  # using empty api_key for now
    path = event['path']
    LOG.info("path='{}'".format(path))

    if path.startswith('/survey'):
        response = get_response(path=path, api_key=api_key)
        print('remaining quota of {}={}'.format(response.key, response.quota))

        body = {
            'data': response.data,
            'quota': response.quota
        }

        if response.quota > 0:
            body['status_code'] = 200
            body['message'] = 'Hello, CDK!  You have hit {}\n'.format(path),
        else:
            body['status_code'] = 429
            body['message'] = 'quota is exceeded for path {}'.format(path)
    else:
        body = {
            'status_code': 400,
            'message': "'{}' is not a valid resource".format(path)
        }

    # can't reach dynamodb with vpc now - needs a NAT or service endpoint
    # but, redis
    # table.update_item(
    #     Key={'path': event['path']},
    #     UpdateExpression='SET hits = if_not_exists(hits, :zero) + :inc, last_hit = :t',
    #     ExpressionAttributeValues={':zero': 0, ':inc': 1, ':t': str(datetime.utcnow())}
    # )

    print('returning {}'.format(
        {
            'statusCode': body['status_code'],
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': body
        }
    ))

    return {
        'statusCode': body['status_code'],
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': body
    }


def get_response(path: str, api_key: str) -> namedtuple:
    """
    get response data
    :param path: request path
    :param api_key: api_key or ''
    :return:
    """
    key = make_key(path, api_key)
    new_key_value = increment_key(key)

    return Response(status_code=200, data={'data': 'something'}, key=key, quota=new_key_value)


def make_key(path: str, api_key: str)-> str:
    """
    make key from path and api_key
    :param path: request path
    :param api_key: api_key or ''
    :return: storage key
    """
    LOG.info('pattern.findall({})={}'.format(path, re.findall(pattern, path)))
    path_parts = re.findall(pattern, path)
    LOG.info('path_parts={}'.format(path_parts))
    key = ':'.join([*path_parts, api_key])
    LOG.info('redis key={}'.format(key))
    return key


def key_quota(key: str)-> int:
    """
    get quota for key
    :param key: key name
    :return: int showing quota count or -1 if not defined
    """
    resource_key = key.split(':')[:-1]  # strip off api_key
    try:
        quota = thresholds[resource_key]['count']
    except KeyError as e:
        LOG.info('resource_key {} not found in thresholds'.format(resource_key))
        quota = -1

    return quota

# TODO set to 'count' and set expire when key created, decrement instead
def increment_key(key: str) -> int:
    """
    increment resource count key
    :param key: item key
    :return: key value after incr
    """
    if r.exists(key):
        value = r.incr(key)
    else:
        value = r.incr(key)
        # r.expire(key, thresholds['global']['interval'])  # set ttl

    return value
