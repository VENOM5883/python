import socket
import threading

import pytest

from client import PolicyClient
from exceptions import ProtocolError
from protocol import decode, encode, make_request, validate_request
from repository import PolicyRepository
from server import serve
from service import PolicyService


def test_encode_decode_message():
    message = make_request("get", {"id": 5}, "abc-123")
    raw = encode(message)
    assert raw.endswith(b"\n")
    assert decode(raw.strip()) == message


def test_invalid_messages():
    with pytest.raises(ProtocolError):
        decode(b"{not json")
    with pytest.raises(ProtocolError):
        validate_request({"command": "drop_database"})


def test_integration_client_tcp_server():
    """Client -> TCP -> Server -> Service -> Repository."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    ready, stop = threading.Event(), threading.Event()
    thread = threading.Thread(target=serve, kwargs=dict(
        port=port, service=PolicyService(PolicyRepository()), ready=ready, stop=stop), daemon=True)
    thread.start()
    assert ready.wait(5)
    client = PolicyClient(port=port)
    try:
        created = client.request("create", {"holder": "Тест", "insurance_type": "health",
                                            "insured_value": 100000, "term_months": 6})
        assert created["status"] == "ok"
        cost = client.request("calculate_cost", {"id": created["data"]["id"]})
        assert cost["data"]["cost"] == 3000.0
        assert client.request("get", {"id": 42})["status"] == "error"
        assert client.request("ping")["data"]["message"] == "pong"
    finally:
        client.close()
        stop.set()
        thread.join(5)
