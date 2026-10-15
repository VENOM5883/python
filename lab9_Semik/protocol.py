"""Прикладной протокол: newline-delimited JSON.

Запрос:  {"request_id": "...", "command": "...", "data": {...}}\n
Ответ:   {"request_id": "...", "status": "ok", "data": ...}\n
         {"request_id": "...", "status": "error", "error": "..."}\n
"""
import json
import socket

from exceptions import ProtocolError

ENCODING = "utf-8"
DELIMITER = b"\n"
MAX_MESSAGE = 1024 * 1024
COMMANDS = {"list", "get", "create", "update", "delete", "calculate_cost", "ping"}


def encode(message: dict) -> bytes:
    return json.dumps(message, ensure_ascii=False).encode(ENCODING) + DELIMITER


def decode(raw: bytes) -> dict:
    try:
        message = json.loads(raw.decode(ENCODING))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError(f"Invalid JSON: {error}") from error
    if not isinstance(message, dict):
        raise ProtocolError("Message must be a JSON object")
    return message


def make_request(command: str, data: dict | None = None, request_id: str = "") -> dict:
    return {"request_id": request_id, "command": command, "data": data or {}}


def validate_request(message: dict) -> tuple[str, dict]:
    command = message.get("command")
    if not command:
        raise ProtocolError("Field 'command' is required")
    if command not in COMMANDS:
        raise ProtocolError(f"Unknown command: {command}")
    data = message.get("data", {})
    if not isinstance(data, dict):
        raise ProtocolError("Field 'data' must be an object")
    return command, data


def ok(data=None, request_id: str = "") -> dict:
    return {"request_id": request_id, "status": "ok", "data": data if data is not None else {}}


def error(text: str, request_id: str = "") -> dict:
    return {"request_id": request_id, "status": "error", "error": text}


class MessageReader:
    """Собирает сообщения из потока байтов TCP по разделителю \\n."""

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.buffer = b""

    def read(self) -> dict | None:
        while DELIMITER not in self.buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                return None  # соединение закрыто
            self.buffer += chunk
            if len(self.buffer) > MAX_MESSAGE:
                raise ProtocolError("Message too large")
        line, self.buffer = self.buffer.split(DELIMITER, 1)
        return decode(line)
