import json
import os
import logging

import boto3
import redis

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
"""

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

r = redis.Redis(
    host=os.environ['REDIS_ADDRESS'],
    port=os.environ['REDIS_PORT'],
    decode_responses=True
)


def handler(event, context):
    """
    main entry point
    event contains message from orchestrator
    """
    LOG.info('request: {}'.format(json.dumps(event)))