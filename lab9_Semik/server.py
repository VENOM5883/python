"""TCP-сервер страховой компании (вариант 15)."""
import argparse
import logging
import socket
from concurrent.futures import ThreadPoolExecutor

from exceptions import InsuranceError, ProtocolError
from protocol import MessageReader, encode, error, ok, validate_request
from repository import PolicyRepository
from service import PolicyService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("server")

HOST, PORT = "127.0.0.1", 5015
CLIENT_TIMEOUT = 60


def seed(service: PolicyService) -> None:
    service.create({"holder": "Иванов И.И.", "insurance_type": "auto",
                    "insured_value": 1_500_000, "term_months": 12, "status": "active"})
    service.create({"holder": "Петрова А.С.", "insurance_type": "property",
                    "insured_value": 8_000_000, "term_months": 12, "status": "active"})
    service.create({"holder": "Сидоров П.О.", "insurance_type": "travel",
                    "insured_value": 50_000, "term_months": 1})


def dispatch(service: PolicyService, command: str, data: dict):
    if command == "ping":
        return {"message": "pong"}
    if command == "list":
        return [p.to_dict() for p in service.list_policies(data.get("insurance_type"))]
    if "id" not in data and command != "create":
        raise ProtocolError("Field 'data.id' is required")
    if command == "get":
        return service.get(data["id"]).to_dict()
    if command == "create":
        return service.create(data).to_dict()
    if command == "update":
        fields = {k: v for k, v in data.items() if k != "id"}
        return service.update(data["id"], fields).to_dict()
    if command == "delete":
        service.delete(data["id"])
        return {"deleted": data["id"]}
    if command == "calculate_cost":
        return service.calculate_cost(data["id"], data.get("driver_experience"),
                                      data.get("claims", 0))
    raise ProtocolError(f"Unknown command: {command}")


def handle_request(service: PolicyService, message: dict) -> dict:
    request_id = str(message.get("request_id", ""))
    try:
        command, data = validate_request(message)
        log.info("Command: %s %s", command, data)
        result = ok(dispatch(service, command, data), request_id)
        log.info("Command %s executed successfully", command)
        return result
    except (ProtocolError, InsuranceError, ValueError, TypeError) as exc:
        log.warning("Bad request: %s", exc)
        return error(str(exc), request_id)


def handle_client(conn: socket.socket, address, service: PolicyService) -> None:
    client = f"{address[0]}:{address[1]}"
    log.info("Client connected: %s", client)
    conn.settimeout(CLIENT_TIMEOUT)
    reader = MessageReader(conn)
    with conn:
        while True:
            try:
                message = reader.read()
                if message is None:
                    break
                response = handle_request(service, message)
            except ProtocolError as exc:
                log.warning("Protocol error from %s: %s", client, exc)
                response = error(str(exc))
            except socket.timeout:
                log.info("Client %s timed out", client)
                break
            except (ConnectionResetError, BrokenPipeError):
                log.info("Connection with %s reset", client)
                break
            try:
                conn.sendall(encode(response))
            except OSError:
                break
    log.info("Client disconnected: %s", client)


def serve(host: str = HOST, port: int = PORT, service: PolicyService | None = None,
          ready=None, stop=None) -> None:
    service = service or PolicyService(PolicyRepository())
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server, \
            ThreadPoolExecutor(max_workers=10) as executor:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        server.settimeout(1.0)  # чтобы периодически проверять флаг остановки
        log.info("Server started on %s:%s", host, port)
        if ready:
            ready.set()
        try:
            while not (stop and stop.is_set()):
                try:
                    conn, address = server.accept()
                except socket.timeout:
                    continue
                executor.submit(handle_client, conn, address, service)
        except KeyboardInterrupt:
            log.info("Server stopped by user")
    log.info("Server shut down")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    service = PolicyService(PolicyRepository())
    seed(service)
    serve(port=args.port, service=service)
