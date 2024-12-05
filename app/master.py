import os
import time
import random
import asyncio
import logging
import itertools
from fastapi import FastAPI
from pydantic import BaseModel
from aiohttp import ClientSession, ClientError


logger = logging.getLogger(__name__)


class Item(BaseModel):
    ''' client POST request in addition to the message
        should also contain write concern parameter wc=1,2,3,..,n
        wc value specifies how many ACKs the master should receive
        from secondaries before responding to the client

        wc = 1 - only from master
        wc = 2 - from master and one secondary
        wc = 3 - from master and two secondarie
    '''
    wc: int
    text: str


class Health(BaseModel):
    ''' inpit item for hertbeat
        ip - ip of slave node that made heartbeat
        delivered - the number of delivered messages that follow each other without gaps
    '''
    ip: str
    delivered: int


# time to repeat heartbeats
HEARTBEATS = float(os.getenv("HEARTBEATS", 3))

app = FastAPI()

# storage for messages in memory
messages = list()

''' storage for secodaries in memory

    example:

    { '172.10.0.3': {               - ip of slave node that made heartbeat
        'delivered': 2,             - the number of delivered messages that follow each other without gaps
        'uptime': 1731878659.010422 - time on this node for this record
        }
    }
'''
slaves = dict()


def get_host_delivered(ip):
    ''' Return the number of delivered messages.
    '''
    return slaves[ip]['delivered']


def get_host_status(ip):
    ''' The simple implementation of a heartbeat mechanism to check
        slaves' health (status): Healthy -> Suspected -> Unhealthy.
    '''
    delta = time.time() - slaves[ip]['uptime']
    if delta > HEARTBEATS * 1.25:
        return 'Unhealthy'
    elif delta < HEARTBEATS * 0.75:
        return 'Healthy'
    else:
        return 'Suspected'


def not_quorum(quorum):
    ''' Check quorum for slaves and +1 for master
        return True if NOT quorum
    '''
    return quorum > (sum([get_host_status(ip) != 'Unhealthy' for ip in slaves.keys()]) + 1)


def get_retry_timeout(attempt):
    ''' return the timeout for the next retry
    '''
    # random.seed(HEARTBEATS)
    step = HEARTBEATS / 100
    main_part = min(300, step * 2 ** attempt)
    random_part = random.random() * main_part * 0.1
    if main_part < 300:
        return round(main_part + random_part, 4)
    else:
        return round(main_part - random_part, 4)


async def replicate(url, data, timeout):
    ''' replicate data to the specified URL using the aiohttp
    '''
    async with ClientSession() as session:
        logger.info(f'--- Replicate to "{url}" data "{data}"')
        try:
            response = await session.post('http://' + url + ':8000', json=data, timeout=timeout)
            return response.status == 200
        except ClientError:
            return False
        except asyncio.TimeoutError:
            return False


async def retry(url, data):
    ''' Retries can be implemented with an unlimited number of attempts
        but, possibly, with some “smart” delays logic
    '''
    response = False
    attempt = 0
    while not response:
        timeout = get_retry_timeout(attempt)
        logger.info(f'-- Retry to "{url}" attempt #"{attempt} with timeout "{timeout}"')
        response = await replicate(url, data, timeout)
        if not response:
            await asyncio.sleep(timeout)
            # check heartbeat information before the next retry
            if get_host_delivered(url) >= (data['id'] - 1):
                response = True
        attempt += 1


@app.get("/")
async def get_messages():
    ''' returns all messages from the in-memory lis
    '''
    return messages


@app.post("/")
async def post_message(item: Item):
    ''' appends a message into the in-memory list
    '''
    if not_quorum(item.wc):
        # If there is no quorum the master should be switched into read-only mode
        # and shouldn’t accept messages append requests and should return the appropriate message
        return {'ask': 0, 'text': 'does not have a quorum'}

    global messages

    #  Add logic for message deduplication and guarantee the total ordering of messages by 'id.'
    data = {"id": len(messages), "text": item.text}
    messages.append(item.text)

    # after each POST request, the message should be replicated on every Secondary server
    logger.info(f'- Send to slaves the "{data}"')
    tasks = [asyncio.create_task(retry(url, data)) for url in slaves.keys() if get_host_status(url) != 'Unhealthy']

    # `item.wc-1` value specifies how many ACKs the master should receive from secondaries before responding to the client
    for task in itertools.islice(asyncio.as_completed(tasks), item.wc-1):
        await task

    return {'ask': 1, "text": item.text, "id": len(messages) - 1}


@app.get("/health")
async def get_health():
    ''' You should have an API on the master to check the slaves’ status: GET /health
    '''
    report = list()
    for ip in sorted(slaves.keys()):
        report.append({'ip': ip, 'status': get_host_status(ip)})

    return report


@app.post("/health")
async def post_health(health: Health):
    ''' Record heartbeat and (if needed) replicate missed messages
    '''
    global slaves
    slaves[health.ip] = {'delivered': health.delivered, 'uptime': time.time()}

    # All messages that secondaries have missed due to unavailability should be replicated after (re)joining the master
    for id in range(health.delivered, len(messages)):
        data = {"id": id, "text": messages[id]}
        logger.info(f'- Answer heartbeat to "{health.ip}"')
        asyncio.create_task(replicate(health.ip, data, HEARTBEATS-0.01))
        await asyncio.sleep(0)

    return {'ask': 1, 'ip': health.ip}
