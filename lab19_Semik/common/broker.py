"""Брокер сообщений для асинхронных событий.

* RabbitMQ (fanout-exchange pharmacy.events) — если задан RABBITMQ_URL (docker compose);
* файловая очередь — локальная имитация брокера без Docker (каждое событие — JSON-файл);
* в памяти — для тестов.
"""
import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("broker")
EXCHANGE = "pharmacy.events"


def make_event(event_type: str, payload: dict) -> dict:
    return {"event_id": str(uuid.uuid4()), "type": event_type,
            "created_at": datetime.now(timezone.utc).isoformat(), "payload": payload}


class InMemoryBroker:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish(self, event_type: str, payload: dict) -> dict:
        event = make_event(event_type, payload)
        self.events.append(event)
        return event


class FileBroker:
    def __init__(self, directory: str) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def publish(self, event_type: str, payload: dict) -> dict:
        event = make_event(event_type, payload)
        tmp = self.directory / f".{event['event_id']}.tmp"
        tmp.write_text(json.dumps(event, ensure_ascii=False), encoding="utf-8")
        tmp.rename(self.directory / f"{time.time_ns()}_{event['event_id']}.json")  # атомарная публикация
        log.info("Опубликовано событие %s", event_type)
        return event

    def consume(self, handler: Callable[[dict], None], poll: float = 0.5, stop=None) -> None:
        while not (stop and stop.is_set()):
            for path in sorted(self.directory.glob("*.json")):
                handler(json.loads(path.read_text(encoding="utf-8")))
                path.unlink()
            time.sleep(poll)


class RabbitBroker:
    def __init__(self, url: str) -> None:
        import pika
        self.pika = pika
        self.parameters = pika.URLParameters(url)

    def _channel(self):
        connection = self.pika.BlockingConnection(self.parameters)
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="fanout", durable=True)
        return connection, channel

    def publish(self, event_type: str, payload: dict) -> dict:
        event = make_event(event_type, payload)
        connection, channel = self._channel()
        try:
            channel.basic_publish(exchange=EXCHANGE, routing_key="", body=json.dumps(event, ensure_ascii=False),
                                  properties=self.pika.BasicProperties(delivery_mode=2))
        finally:
            connection.close()
        log.info("Опубликовано событие %s в RabbitMQ", event_type)
        return event

    def consume(self, handler: Callable[[dict], None], queue: str = "notifications", stop=None) -> None:
        while True:
            try:
                connection, channel = self._channel()
                channel.queue_declare(queue=queue, durable=True)
                channel.queue_bind(queue=queue, exchange=EXCHANGE)

                def on_message(ch, method, _props, body):
                    handler(json.loads(body))
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                channel.basic_consume(queue=queue, on_message_callback=on_message)
                channel.start_consuming()
            except Exception as error:  # noqa: BLE001 — брокер ещё не поднялся
                log.warning("RabbitMQ недоступен (%s), повтор через 3 c", error)
                time.sleep(3)


def create_broker():
    url = os.getenv("RABBITMQ_URL")
    if url:
        return RabbitBroker(url)
    return FileBroker(os.getenv("EVENTS_DIR", str(Path(__file__).resolve().parents[1] / ".events")))
