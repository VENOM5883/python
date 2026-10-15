from fastapi.testclient import TestClient

from app.main import create_app
from common.broker import FileBroker, make_event


def test_handler_creates_notification_and_is_idempotent():
    app = create_app("sqlite://", start_consumer=False)
    event = make_event("OrderCreated", {"id": "abc", "customer": "Семик А.", "total": 445.0})
    assert app.state.handler(event).recipient == "Семик А."
    assert app.state.handler(event) is None          # повторная доставка не дублирует уведомление
    data = TestClient(app).get("/notifications").json()
    assert len(data) == 1 and "abc" in data[0]["text"]


def test_unknown_event_ignored():
    app = create_app("sqlite://", start_consumer=False)
    assert app.state.handler(make_event("Something", {})) is None


def test_consumer_reads_file_broker(tmp_path):
    broker = FileBroker(str(tmp_path))
    broker.publish("OrderCancelled", {"id": "x1", "customer": "Иванов И."})
    with TestClient(create_app("sqlite://", broker=broker)) as client:
        import time
        for _ in range(20):
            if client.get("/notifications").json():
                break
            time.sleep(0.1)
        assert client.get("/notifications", params={"recipient": "Иванов И."}).json()[0]["type"] == "OrderCancelled"
