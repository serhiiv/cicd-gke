import os
import socket
import asyncio
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from aiohttp import ClientSession, ClientError
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class Item(BaseModel):
    # inpit item for message
    id: int
    text: str


class Sleep(BaseModel):
    # inpit time for delay
    time: float


# own local ip
IP = socket.gethostbyname(socket.gethostname())

# time to repeat heartbeats
HEARTBEATS = float(os.getenv("HEARTBEATS", 3))


async def beat(session):
    ''' one heartbeat to the master
        sent ip and amount received valid messages
    '''
    # count valid messages
    with_none = messages + [None]
    delivered = len(with_none[0: with_none.index(None)])

    data = {"ip": IP, "delivered": delivered}
    try:
        logger.info(f'= Heartbeats with "{data}"')
        await session.post('http://master:8000/health', json=data, timeout=HEARTBEATS)
    except ClientError:
        pass


async def heart():
    ''' an endless cycle of heartbeats
    '''
    async with ClientSession() as session:
        while True:
            asyncio.create_task(beat(session))
            await asyncio.sleep(HEARTBEATS)


@asynccontextmanager
async def heartbeats(app: FastAPI):
    ''' Start heart procedure before startup slave node
    '''
    asyncio.create_task(heart())
    yield


app = FastAPI(lifespan=heartbeats)
# storage for messages in memory
messages = list()

# time for the delay this node
delay = Sleep(time=0)


@app.get("/")
async def get_messages():
    ''' Returns all replicated messages from the in-memory list
        until the first message with 'None' happens.
    '''
    out = messages + [None]
    return out[0: out.index(None)]


@app.post("/")
async def post_message(item: Item):
    ''' appends a message into the in-memory list
    '''
    global messages

    # Fill the list of messages with values ​​'None' up to the end
    # and make the list length of the messages equal to the 'id.'
    messages += [None] * (item.id - len(messages) + 1)
    messages[item.id] = item.text
    logger.info(f'== Add message "{item}"')

    # Make a timeout before the response.
    await asyncio.sleep(delay.time)

    return {"ask": 1, "item": item}


@app.get("/sleep")
async def get_sleep():
    ''' Return the time for the delay of this node.
    '''
    return {"sleep": delay}


@app.post("/sleep")
async def post_sleep(sleep: Sleep):
    ''' Set the time for the delay of this node.
    '''
    global delay
    delay = sleep
    logger.info(f'== Set sleep {delay}')
    return {"sleep": delay}
