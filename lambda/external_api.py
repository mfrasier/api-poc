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

Response = namedtuple('Response', ['status_code', 'data', 'key', 'quota', 'message'])

# throttle thresholds
thresholds = {
    'global': {
        'interval': 60,
    },
    'survey': {
        'count': 20
    },
    'survey:interview': {
        'count': 10
    },
    'survey:interview:attachment': {
        'count': 5
    }
}


# match incoming path to ascertain resource
# pattern=re.compile(r'^/(survey)(?:/)?(?:/\d*)?/(interview)(?:/)?(?:/\d*)/(attachment)(?:/)?(?:\d*)?')
pattern = r'/([a-zA-Z]+)'

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT']
)


def handler(event, context):
    """
    main entry point
    event contains dict from api gateway request
    """
    LOG.info('request: {}'.format(json.dumps(event)))
    LOG.info('redis address: {}'.format(os.environ['REDIS_ADDRESS']))

    api_key = 'none'  # using empty api_key for now
    path = event['path']
    LOG.info(f"path='{path}'")

    if path.startswith('/survey'):
        response = get_response(location=path, api_key=api_key)
        LOG.info(f'response={response}')
        LOG.info(f'remaining quota of {response.key}={response.quota}')

        body = {
            'data': response.data,
            'quota': response.quota
        }

        if response.quota > 0:
            body['status_code'] = 200
            body['message'] = 'Hello, CDK!  You have hit {}\n'.format(path),
        else:
            body['status_code'] = 429
            body['message'] = response.message
    else:
        body = {
            'status_code': 400,
            'message': f"'{path}' is not a valid resource"
        }

    return {
        'statusCode': body['status_code'],
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }


def get_response(location: str, api_key: str) -> namedtuple:
    """
    get response data
    :param location: request path
    :param api_key: api_key or ''
    :return:
    """
    key = make_key(location, api_key)
    exceeded, location = quota_exceeded(key)

    if exceeded:
        response = Response(status_code=200, data={'data': 'something'}, key=key, quota=0,
                            message=f'quota exceeded at {location}')
    else:
        new_key_value = int(decrement_key(key))
        response = Response(status_code=200, data={'data': 'something'}, key=key, quota=new_key_value, message='ok')

    return response


def quota_exceeded(key:str)-> 'tuple':
    """
    check quota of key and parent paths
    :param key:
    :return: True if quota exceeded, otherwise False
    """
    resources, api_key = list(key.split(':')[:-1]), key.split(':')[-1:][0]

    LOG.info(f'resources: {resources}')
    for end in range(len(resources) - 1, 0, -1):
        parent_key = ':'.join([*resources[:-end], api_key])
        LOG.debug(f'checking exceeded quota for resource_key: {parent_key}')
        parent_quota = key_value(parent_key)
        LOG.debug(f'quota for {parent_key}={parent_quota}')
        if parent_quota is not None and int(parent_quota) == 0:
            return True, parent_key

    quota = key_value(key)
    LOG.debug(f'quota for {key}={quota}')
    if quota is not None and int(r.get(key)) <= 0:
        return True, key

    return False, key


def key_value(key: str)-> int:
    """
    get value of key
    if key doesn't exist
      create it with threshold value
      set expiration
    :param key:
    :return: value of key
    """
    if r.get(key) is None:
        expiration = thresholds['global']['interval']
        quota = key_quota(key)
        LOG.info(f'key {key} does not exist - setting value to {quota} and expiration {expiration}')
        r.set(key, quota)
        r.expire(key, expiration)  # set ttl

    return int(r.get(key))

def make_key(path: str, api_key: str)-> str:
    """
    make key from path and api_key
    :param path: request path
    :param api_key: api_key or ''
    :return: storage key
    """
    path_parts = re.findall(pattern, path)
    key = ':'.join([*path_parts, api_key])
    LOG.debug('redis key={}'.format(key))
    return key


def key_quota(key: str)-> int:
    """
    get quota for key
    :param key: key name
    :return: int showing quota count or -1 if not defined
    """
    resource_key = ':'.join(key.split(':')[:-1])  # strip off api_key
    try:
        quota = thresholds[resource_key]['count']
    except KeyError as e:
        LOG.info('resource_key {} not found in thresholds'.format(resource_key))
        quota = -1

    return quota


def decrement_key(key: str) -> int:
    """
    walk down resource path composite keys
      if key not exist, set to threshold count and set expire
      decrement resource count key
    :param key: item key
    :return: key value after decrement of last key
    """
    # decrement parent keys
    resources, api_key = list(key.split(':')[:-1]), key.split(':')[-1:][0]
    for end in range(len(resources) - 1, 0, -1):
        parent_key = ':'.join([*resources[:-end], api_key])
        if r.exists(parent_key):
            LOG.debug(f'decrementing parent key {parent_key}')
            r.decr(parent_key)
        else:
            key_value(parent_key)
            LOG.debug(f'decrementing new parent key {parent_key}')
            r.decr(parent_key)

    # decrement leaf key
    value = key_value(key)
    r.decr(key)
    return value
