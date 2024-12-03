from fastapi.testclient import TestClient
from app.slave import app, HEARTBEATS


client = TestClient(app)


def test_root():
    # check the HEARTBEATS
    assert HEARTBEATS == 3.0

    # get the initial list of messages
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == []

    # add the second message
    response = client.post("/", json={"id": 1, "text": "message 1"})
    assert response.status_code == 200
    assert response.json() == {'ask': 1, 'item': {'id': 1, 'text': 'message 1'}}

    # check zero list
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == []

    # add the first message
    response = client.post("/", json={"id": 0, "text": "message 0"})
    assert response.status_code == 200
    assert response.json() == {'ask': 1, 'item': {'id': 0, 'text': 'message 0'}}

    # check two messages in the list
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == ['message 0', 'message 1']


def test_sleep():
    # get the initial sleep time
    response = client.get("/sleep")
    assert response.status_code == 200
    assert response.json() ==  {'sleep': {'time': 0}}

    # set sleep time
    response = client.post("/sleep", json={"time": 0.99})
    assert response.status_code == 200
    assert response.json() ==  {'sleep': {'time': 0.99}}

    # check sleep time
    response = client.get("/sleep")
    assert response.status_code == 200
    assert response.json() == {'sleep': {'time': 0.99}}
