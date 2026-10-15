"""Демонстрация тайм-аута: «зависший» сервер принимает соединение, но не отвечает."""
import socket
import threading

from client import PolicyClient


def silent_server(sock: socket.socket) -> None:
    conn, _ = sock.accept()
    threading.Event().wait(10)  # ничего не отвечаем
    conn.close()


if __name__ == "__main__":
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    threading.Thread(target=silent_server, args=(server,), daemon=True).start()
    client = PolicyClient(port=server.getsockname()[1], timeout=2)
    try:
        client.request("ping")
    except socket.timeout:
        print("Операция завершилась по тайм-ауту (2 сек): сервер не ответил")
    finally:
        client.close()
