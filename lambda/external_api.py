import json
import os
import logging
from collections import namedtuple

import redis

"""
Simulate an external RESTful API service with client throttling
"""
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

Response = namedtuple('Response', ['status_code', 'data', 'quota_exceeded', 'message'])

# quota threshold counts - ttl in seconds
quotas = dict(
    second={'ttl': 1, 'quota': 2},
    minute={'ttl': 60, 'quota': 60 * 2},
    hour={'ttl': 60 * 60, 'quota': 60 * 60 * 2},
    day={'ttl': 60 * 60 * 24, 'quota': 60 * 60 * 24 * 2}
)

# match incoming path to ascertain resource
pattern = r'/([a-zA-Z]+)'

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT'],
    decode_responses=True
)


def handler(event, context):
    """
    main entry point
    event contains dict from api gateway request
    """
    # LOG.info('request: {}'.format(json.dumps(event)))
    LOG.info('redis address: {}'.format(os.environ['REDIS_ADDRESS']))

    api_key = 'none'  # using empty api_key for now
    path = event['path']
    http_method = event['httpMethod']
    LOG.info(f"path='{path}', method={http_method}")

    if http_method == 'GET':
        if path.startswith('/survey'):
            response = get_response(api_key)
            LOG.info(f'response={response}')

            body = {
                'data': response.data,
                'quota_exceeded': response.quota_exceeded
            }

            if response.quota_exceeded:
                body['status_code'] = 429
                body['message'] = response.message
            else:
                body['status_code'] = 200
                body['message'] = 'Hello, CDK!  You have hit {}\n'.format(path),
        elif path == '/keys':
            key_data = {'keys': []}
            for key in sorted(r.keys()):
                key_data['keys'].append({
                    'name': key,
                    'value': r.get(key),
                    'ttl': r.ttl(key)
                })

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(key_data)
            }
        elif path == '/stats/invoke':
            # convenience function to get orchestrator invoke stats
            stats = r.hgetall('stats:invoke')
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(stats)
            }
        elif path == '/health':
            """return status 429 if quota exceeded, 200 otherwise"""
            exceeded, interval = quota_exceeded(api_key)
            if exceeded:
                message = f"quota exceeded at {interval} interval"
            else:
                message = "quota ok"
            body = {
                'status_code': 429 if exceeded else 200,
                'message': message
            }
        else:
            body = {
                'status_code': 400,
                'message': f"'{path}' is not a valid resource.  Try /survey/1/interview/1/attachment/1 or /list_keys"
            }

        return {
            'statusCode': body['status_code'],
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(body)
        }
    elif http_method == 'DELETE':
        if path == '/keys':
            for key in r.keys('quota:*'):
                r.delete(key)
                LOG.info('deleted key {}'.format(key))
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': 'cache cleared of keys matching survey:*'
                }
    else:
        response = {
            'status_code': 405,
            'message': f"HTTP method '{http_method}' is not a supported method.  Try GET"
        }
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response)
        }


def get_response(api_key: str) -> namedtuple:
    """
    get response data
    :param api_key: api_key or ''
    :return:
    """
    exceeded, interval = quota_exceeded(api_key)

    if exceeded:
        response = Response(status_code=200, data={}, quota_exceeded=exceeded,
                            message=f'{interval} quota exceeded')
    else:
        response = Response(status_code=200, data={'data': 'something'}, quota_exceeded=exceeded, message='ok')
        decrement_keys(api_key)

    return response


def quota_exceeded(api_key: str) -> tuple:
    """
    check quota of key for each time interval
    :param api_key:
    :return: True if quota exceeded, otherwise False
    """
    expired_interval = None

    for interval in quotas.keys():
        interval_key = ':'.join([api_key, interval])
        if key_value(interval_key) <= 0:
            expired_interval = interval

    return expired_interval is not None, expired_interval


def key_value(key: str) -> int:
    """
    get value of key
    if key doesn't exist
      create it with threshold value and expiration
    :param key: the key
    :return: value of key
    """
    if not r.exists(key):
        set_expiry_and_quota(key)
    else:
        if r.ttl(key) == -1:
            LOG.info(f'key {key} exists but has no expiry - setting new value and expiration')
            set_expiry_and_quota(key)

    return int(r.get(key))


def set_expiry_and_quota(key: str) -> None:
    """
    Set quota value and expiration on key atomically
    :param key: key string
    :return: nothing
    """
    interval = key.split(':')[-1:][0]
    quota = quotas[interval]

    # using a pipeline here to make atomic
    # pipeline = r.pipeline().set(key, quota['quota']).expire(key, quota['ttl'])
    # pipeline.execute()
    r.set(key, quota['quota'], quota['ttl'])
    LOG.info(f"set key {key} quota={quota['quota']} and ttl={quota['ttl']}")


def decrement_keys(api_key: str) -> None:
    """
    walk down resource path composite keys
      if key not exist, set to threshold count and set expire
      decrement resource count key
    :param api_key: item key
    :return: key value after decrement of last key
    """
    # decrement keys
    for interval in quotas.keys():
        interval_key = ':'.join([api_key, interval])
        if r.exists(interval_key):
            r.decr(interval_key)
        else:
            key_value(interval_key)
            r.decr(interval_key)
