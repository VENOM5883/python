"""TCP-клиент страховой компании (вариант 15)."""
import argparse
import itertools
import json
import socket

from exceptions import ProtocolError
from protocol import MessageReader, encode, make_request

HOST, PORT, TIMEOUT = "127.0.0.1", 5015, 5


class PolicyClient:
    def __init__(self, host: str = HOST, port: int = PORT, timeout: float = TIMEOUT) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.reader = MessageReader(self.sock)
        self._ids = itertools.count(1)

    def request(self, command: str, data: dict | None = None) -> dict:
        self.sock.sendall(encode(make_request(command, data, f"req-{next(self._ids)}")))
        response = self.reader.read()
        if response is None:
            raise ConnectionError("Server closed the connection")
        return response

    def close(self) -> None:
        self.sock.close()


def ask_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Введите целое число")


def policy_fields(partial: bool) -> dict:
    hint = " (Enter — не менять)" if partial else ""
    raw = {
        "holder": input(f"Страхователь{hint}: ").strip(),
        "insurance_type": input(f"Тип (auto/property/travel/health){hint}: ").strip(),
        "insured_value": input(f"Страховая сумма{hint}: ").strip(),
        "term_months": input(f"Срок, мес.{hint}: ").strip(),
    }
    if partial:
        raw["status"] = input(f"Статус (draft/active/expired/cancelled){hint}: ").strip()
    return {k: v for k, v in raw.items() if v} if partial else raw


def print_response(response: dict) -> None:
    if response.get("status") == "ok":
        print(json.dumps(response["data"], ensure_ascii=False, indent=2))
    else:
        print("ОШИБКА СЕРВЕРА:", response.get("error"))


MENU = """
=== CLIENT: страховые полисы ===
1. Получить список
2. Получить полис
3. Создать
4. Изменить
5. Удалить
6. Расчёт стоимости полиса
7. Ping
8. Отправить произвольный JSON
0. Выход"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    try:
        client = PolicyClient(port=args.port)
    except OSError as exc:
        print(f"Сервер недоступен: {exc}")
        return
    try:
        while True:
            print(MENU)
            choice = input("Введите команду: ").strip()
            if choice == "0":
                break
            if choice == "1":
                kind = input("Фильтр по типу (Enter — все): ").strip()
                response = client.request("list", {"insurance_type": kind} if kind else {})
            elif choice == "2":
                response = client.request("get", {"id": ask_int("ID: ")})
            elif choice == "3":
                response = client.request("create", policy_fields(False))
            elif choice == "4":
                response = client.request("update", {"id": ask_int("ID: "), **policy_fields(True)})
            elif choice == "5":
                response = client.request("delete", {"id": ask_int("ID: ")})
            elif choice == "6":
                data = {"id": ask_int("ID: "), "claims": ask_int("Страховых случаев ранее: ")}
                experience = input("Стаж водителя, лет (для auto, Enter — пропустить): ").strip()
                if experience.isdigit():
                    data["driver_experience"] = int(experience)
                response = client.request("calculate_cost", data)
            elif choice == "7":
                response = client.request("ping")
            elif choice == "8":
                client.sock.sendall(input("JSON: ").encode("utf-8") + b"\n")
                response = client.reader.read() or {}
            else:
                print("Неизвестная команда")
                continue
            print_response(response)
    except socket.timeout:
        print("Тайм-аут: сервер не ответил вовремя")
    except (ConnectionError, ProtocolError, OSError) as exc:
        print("Соединение разорвано:", exc)
    finally:
        client.close()


if __name__ == "__main__":
    main()
