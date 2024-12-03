import time
import random
from fastapi.testclient import TestClient
from app.master import app, HEARTBEATS
from app.master import get_host_status, not_quorum, get_retry_timeout, get_host_delivered


client = TestClient(app)


def test_root():
    # check the HEARTBEATS
    assert HEARTBEATS == 3.0

    random.seed(HEARTBEATS)
    assert round(get_retry_timeout(0), 4) == 0.0307
    assert round(get_retry_timeout(20), 4) == 283.6731

    # get the initial list of messages
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == []

    # add the first message
    response = client.post("/", json={"wc": 1, "text": "message 0"})
    assert response.status_code == 200
    assert response.json() == {'ask': 1, 'text': 'message 0', 'id': 0}

    # check the messages in the list
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == ['message 0']


def test_health():
    # get the initial list of messages
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == list()

    # add the first host
    response = client.post("/health", json={"ip": "slave_1", "delivered": 0})
    assert response.status_code == 200
    assert response.json() == {'ask': 1, 'ip': 'slave_1'}

    assert get_host_delivered("slave_1") == 0

    # get the list of messages
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == [{'ip': 'slave_1', 'status': 'Healthy'}]


def test_status_quorum_function():

    assert get_host_status('slave_1') == 'Healthy'
    assert not not_quorum(1)
    assert not not_quorum(2)
    time.sleep(HEARTBEATS)
    assert get_host_status('slave_1') == 'Suspected'
    assert not not_quorum(1)
    assert not not_quorum(2)
    time.sleep(HEARTBEATS)
    assert get_host_status('slave_1') == 'Unhealthy'
    assert not not_quorum(1)
    assert not_quorum(2)

    # get the list of messages
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == [{'ip': 'slave_1', 'status': 'Unhealthy'}]

    # add message
    response = client.post("/", json={"wc": 2, "text": "message does not have a quorum"})
    assert response.status_code == 200
    assert response.json() == {'ask': 0, 'text': 'does not have a quorum'}

    # add the first host
    response = client.post("/health", json={"ip": "slave_1", "delivered": 0})
    assert response.status_code == 200
    assert response.json() == {'ask': 1, 'ip': 'slave_1'}

    # get the list of messages
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == [{'ip': 'slave_1', 'status': 'Healthy'}]
